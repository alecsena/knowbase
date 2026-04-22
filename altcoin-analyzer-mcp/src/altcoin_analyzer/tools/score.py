from typing import Any

from altcoin_analyzer.scoring.engine import ScoringEngine
from altcoin_analyzer.utils.logging import get_logger

from ._assembler import assemble_altcoin_data

logger = get_logger(__name__)


async def score_altcoin(symbol: str) -> dict[str, Any]:
    """Quantitative scoring only — no LLM call."""
    altcoin_data = await assemble_altcoin_data(symbol.upper())
    engine = ScoringEngine()
    result = engine.score(altcoin_data)
    return result.model_dump()
