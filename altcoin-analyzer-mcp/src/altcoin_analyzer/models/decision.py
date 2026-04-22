from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LLMDecision(BaseModel):
    decision: Literal["BUY", "HOLD", "AVOID"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    key_risks: list[str]
    key_opportunities: list[str]
    suggested_allocation_pct: float = Field(ge=0, le=10)
    stop_loss_suggestion_pct: float = Field(ge=5, le=30)
    reevaluation_trigger: str


class DecisionOutput(BaseModel):
    symbol: str
    name: str
    market_data: dict[str, float | int | str | None]
    scores: dict[str, float]
    decision: Literal["BUY", "HOLD", "AVOID"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    red_flags: list[str]
    green_flags: list[str]
    key_risks: list[str]
    key_opportunities: list[str]
    suggested_allocation_pct: float | None = None
    stop_loss_suggestion_pct: float | None = None
    reevaluation_trigger: str | None = None
    llm_provider_used: str
    metadata: dict[str, str | list[str]]

    DISCLAIMER: str = (
        "⚠️ AVISO: Esta ferramenta é educacional e não constitui aconselhamento financeiro. "
        "Criptoativos são altamente voláteis. Faça sua própria pesquisa (DYOR) e consulte um "
        "profissional qualificado antes de investir."
    )

    @classmethod
    def from_analysis(
        cls,
        altcoin_data: object,
        scoring_result: object,
        llm_decision: "LLMDecision",
        llm_provider: str,
    ) -> "DecisionOutput":
        from altcoin_analyzer.models.altcoin import AltcoinData
        from altcoin_analyzer.models.scoring import ScoringResult

        assert isinstance(altcoin_data, AltcoinData)
        assert isinstance(scoring_result, ScoringResult)

        md = altcoin_data.market_data
        return cls(
            symbol=altcoin_data.symbol,
            name=altcoin_data.name,
            market_data={
                "price_usd": md.price_usd,
                "market_cap_usd": md.market_cap_usd,
                "volume_24h_usd": md.volume_24h_usd,
                "price_change_24h_pct": md.price_change_24h_pct,
                "price_change_7d_pct": md.price_change_7d_pct,
                "price_change_30d_pct": md.price_change_30d_pct,
                "fdv_vs_mcap_ratio": md.fdv_vs_mcap_ratio,
                "liquidity_ratio": md.liquidity_ratio,
            },
            scores={
                "fundamentals": scoring_result.fundamentals.score,
                "on_chain": scoring_result.on_chain.score,
                "market": scoring_result.market.score,
                "risk": scoring_result.risk.score,
                "overall": scoring_result.overall,
            },
            decision=llm_decision.decision,
            confidence=llm_decision.confidence,
            reasoning=llm_decision.reasoning,
            red_flags=scoring_result.red_flags,
            green_flags=scoring_result.green_flags,
            key_risks=llm_decision.key_risks,
            key_opportunities=llm_decision.key_opportunities,
            suggested_allocation_pct=llm_decision.suggested_allocation_pct,
            stop_loss_suggestion_pct=llm_decision.stop_loss_suggestion_pct,
            reevaluation_trigger=llm_decision.reevaluation_trigger,
            llm_provider_used=llm_provider,
            metadata={
                "analyzed_at": datetime.utcnow().isoformat(),
                "data_gaps": altcoin_data.data_gaps,
            },
        )
