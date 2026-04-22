import asyncio
from typing import Any, Literal

from altcoin_analyzer.scoring.engine import ScoringEngine
from altcoin_analyzer.utils.logging import get_logger

from ._assembler import assemble_altcoin_data

logger = get_logger(__name__)


async def compare_altcoins(
    symbols: list[str],
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate",
) -> dict[str, Any]:
    if not (2 <= len(symbols) <= 5):
        return {"error": "symbols must contain between 2 and 5 items"}

    syms = [s.upper() for s in symbols]
    engine = ScoringEngine()

    results_raw = await asyncio.gather(
        *[assemble_altcoin_data(s) for s in syms],
        return_exceptions=True,
    )

    scored: list[dict[str, Any]] = []
    errors: list[str] = []

    for sym, raw in zip(syms, results_raw, strict=False):
        if isinstance(raw, Exception):
            errors.append(f"{sym}: {raw}")
            continue
        scoring = engine.score(raw)
        scored.append({
            "symbol": sym,
            "name": raw.name,
            "overall_score": scoring.overall,
            "fundamentals": scoring.fundamentals.score,
            "on_chain": scoring.on_chain.score,
            "market": scoring.market.score,
            "risk": scoring.risk.score,
            "red_flags_count": len(scoring.red_flags),
            "green_flags_count": len(scoring.green_flags),
            "market_cap_usd": raw.market_data.market_cap_usd,
            "volume_24h_usd": raw.market_data.volume_24h_usd,
            "price_change_30d_pct": raw.market_data.price_change_30d_pct,
        })

    scored.sort(key=lambda x: x["overall_score"], reverse=True)
    for i, item in enumerate(scored):
        item["rank"] = i + 1

    logger.info("altcoins_compared", symbols=syms, count=len(scored))

    return {
        "ranking": scored,
        "errors": errors,
        "risk_profile": risk_profile,
        "disclaimer": (
            "⚠️ AVISO: Esta ferramenta é educacional e não constitui aconselhamento financeiro. "
            "Criptoativos são altamente voláteis. DYOR."
        ),
    }
