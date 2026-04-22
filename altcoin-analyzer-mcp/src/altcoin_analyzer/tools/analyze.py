import time
from typing import Any, Literal

from altcoin_analyzer.llm.client import LLMClient, LLMError
from altcoin_analyzer.llm.prompts import build_decision_prompt
from altcoin_analyzer.models.decision import DecisionOutput
from altcoin_analyzer.scoring.engine import ScoringEngine
from altcoin_analyzer.utils.logging import get_logger

from ._assembler import assemble_altcoin_data

logger = get_logger(__name__)


async def analyze_altcoin(
    symbol: str,
    include_llm_reasoning: bool = True,
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate",
    time_horizon: Literal["short", "medium", "long"] = "medium",
) -> dict[str, Any]:
    start = time.monotonic()
    sym = symbol.upper()

    altcoin_data = await assemble_altcoin_data(sym)

    engine = ScoringEngine()
    scoring_result = engine.score(altcoin_data)

    llm_provider_used = "none"

    if include_llm_reasoning:
        prompt = build_decision_prompt(
            symbol=sym,
            risk_profile=risk_profile,
            time_horizon=time_horizon,
            scores={
                "fundamentals": scoring_result.fundamentals.score,
                "on_chain": scoring_result.on_chain.score,
                "market": scoring_result.market.score,
                "risk": scoring_result.risk.score,
                "overall": scoring_result.overall,
            },
            market_data=altcoin_data.market_data.model_dump(),
            onchain_data=altcoin_data.on_chain.model_dump(),
            red_flags=scoring_result.red_flags,
            green_flags=scoring_result.green_flags,
        )

        client = LLMClient()
        try:
            llm_decision, llm_provider_used = await client.decide(prompt)
        except LLMError as e:
            logger.error("llm_decision_failed", symbol=sym, error=str(e))
            from altcoin_analyzer.models.decision import LLMDecision

            llm_decision = LLMDecision(
                decision="HOLD",
                confidence=0.0,
                reasoning=f"LLM indisponível: {e}. Decisão baseada apenas em scoring quantitativo.",
                key_risks=scoring_result.red_flags[:3],
                key_opportunities=scoring_result.green_flags[:3],
                suggested_allocation_pct=0.0,
                stop_loss_suggestion_pct=15.0,
                reevaluation_trigger="LLM disponível novamente",
            )
            llm_provider_used = "fallback_rule_based"
    else:
        from altcoin_analyzer.models.decision import LLMDecision

        score = scoring_result.overall
        decision: Literal["BUY", "HOLD", "AVOID"] = (
            "BUY" if score >= 7.0 else "AVOID" if score <= 4.0 else "HOLD"
        )
        llm_decision = LLMDecision(
            decision=decision,
            confidence=round(abs(score - 5.5) / 4.5, 2),
            reasoning="LLM desabilitado. Decisão baseada em scoring quantitativo.",
            key_risks=scoring_result.red_flags[:3],
            key_opportunities=scoring_result.green_flags[:3],
            suggested_allocation_pct=max(0, min(10, (score - 5) * 2)),
            stop_loss_suggestion_pct=15.0,
            reevaluation_trigger="Mudança significativa nos scores quantitativos",
        )

    output = DecisionOutput.from_analysis(
        altcoin_data=altcoin_data,
        scoring_result=scoring_result,
        llm_decision=llm_decision,
        llm_provider=llm_provider_used,
    )

    elapsed_ms = round((time.monotonic() - start) * 1000)
    logger.info(
        "altcoin_analyzed",
        symbol=sym,
        overall_score=scoring_result.overall,
        decision=llm_decision.decision,
        latency_ms=elapsed_ms,
        llm_provider=llm_provider_used,
    )

    return output.model_dump()
