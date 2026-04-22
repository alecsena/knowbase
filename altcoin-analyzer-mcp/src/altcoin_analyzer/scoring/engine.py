from altcoin_analyzer.models.altcoin import AltcoinData
from altcoin_analyzer.models.scoring import CategoryScore, CriterionScore, ScoringResult
from altcoin_analyzer.utils.logging import get_logger

from .criteria import CRITERIA_CONFIG
from .weights import DEFAULT_WEIGHTS, CategoryWeights

logger = get_logger(__name__)

RED_FLAG_THRESHOLD = 3.5
GREEN_FLAG_THRESHOLD = 7.5


class ScoringEngine:
    def __init__(self, weights: CategoryWeights | None = None) -> None:
        self._weights = weights or DEFAULT_WEIGHTS

    def score(self, data: AltcoinData) -> ScoringResult:
        category_scores: dict[str, CategoryScore] = {}
        red_flags: list[str] = []
        green_flags: list[str] = []

        weight_map = {
            "fundamentals": self._weights.fundamentals,
            "on_chain": self._weights.on_chain,
            "market": self._weights.market,
            "risk": self._weights.risk,
        }

        for cat_name, cfg in CRITERIA_CONFIG.items():
            criteria_scores: list[CriterionScore] = []
            weighted_sum = 0.0

            for name, weight, source, fn in cfg["criteria"]:
                try:
                    score_val, note = fn(data)
                except Exception as exc:
                    logger.warning("criterion_error", criterion=name, error=str(exc))
                    score_val, note = 5.0, f"error: {exc}"

                cs = CriterionScore(name=name, score=score_val, weight=weight, source=source, note=note)
                criteria_scores.append(cs)
                weighted_sum += score_val * weight

                label = f"[{cat_name}/{name}] {note}"
                if score_val <= RED_FLAG_THRESHOLD:
                    red_flags.append(label)
                elif score_val >= GREEN_FLAG_THRESHOLD:
                    green_flags.append(label)

            cat_score = CategoryScore(
                name=cat_name,
                score=round(weighted_sum, 2),
                weight=weight_map[cat_name],
                criteria=criteria_scores,
            )
            category_scores[cat_name] = cat_score

        overall = round(
            sum(cs.score * cs.weight for cs in category_scores.values()), 2
        )

        result = ScoringResult(
            symbol=data.symbol,
            fundamentals=category_scores["fundamentals"],
            on_chain=category_scores["on_chain"],
            market=category_scores["market"],
            risk=category_scores["risk"],
            overall=overall,
            red_flags=red_flags,
            green_flags=green_flags,
        )

        logger.info(
            "scoring_complete",
            symbol=data.symbol,
            overall=overall,
            red_flags=len(red_flags),
            green_flags=len(green_flags),
        )
        return result

    def update_weights(self, new_weights: CategoryWeights) -> None:
        self._weights = new_weights

    def get_weights(self) -> CategoryWeights:
        return self._weights
