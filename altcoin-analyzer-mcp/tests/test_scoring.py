import pytest

from altcoin_analyzer.models.altcoin import AltcoinData, FundamentalData, MarketData, OnChainData
from altcoin_analyzer.scoring.engine import ScoringEngine
from altcoin_analyzer.scoring.weights import CategoryWeights


def test_scoring_returns_valid_result(sample_altcoin: AltcoinData) -> None:
    engine = ScoringEngine()
    result = engine.score(sample_altcoin)
    assert result.symbol == "SOL"
    assert 0 <= result.overall <= 10
    assert 0 <= result.fundamentals.score <= 10
    assert 0 <= result.on_chain.score <= 10
    assert 0 <= result.market.score <= 10
    assert 0 <= result.risk.score <= 10


def test_scoring_overall_is_weighted_sum(sample_altcoin: AltcoinData) -> None:
    engine = ScoringEngine()
    result = engine.score(sample_altcoin)
    expected = (
        result.fundamentals.score * result.fundamentals.weight
        + result.on_chain.score * result.on_chain.weight
        + result.market.score * result.market.weight
        + result.risk.score * result.risk.weight
    )
    assert abs(result.overall - expected) < 0.01


def test_red_and_green_flags_populated(sample_altcoin: AltcoinData) -> None:
    engine = ScoringEngine()
    result = engine.score(sample_altcoin)
    # Audited + team_known + high volume should generate green flags
    assert isinstance(result.red_flags, list)
    assert isinstance(result.green_flags, list)
    assert len(result.green_flags) > 0


def test_unaudited_coin_generates_red_flag() -> None:
    data = AltcoinData(
        symbol="RUGGED",
        name="Rugged Token",
        coingecko_id="rugged-token",
        market_data=MarketData(
            price_usd=0.001,
            market_cap_usd=100_000,
            fully_diluted_valuation_usd=10_000_000,
            volume_24h_usd=1_000,
            price_change_24h_pct=-50.0,
            price_change_7d_pct=-80.0,
            price_change_30d_pct=-90.0,
            all_time_high_usd=1.0,
            ath_change_pct=-99.9,
            circulating_supply=1_000_000,
            total_supply=10_000_000,
            max_supply=None,
            liquidity_ratio=0.01,
            fdv_vs_mcap_ratio=100.0,
        ),
        on_chain=OnChainData(github_commits_90d=0),
        fundamentals=FundamentalData(is_audited=False, team_known=False),
    )
    engine = ScoringEngine()
    result = engine.score(data)
    assert len(result.red_flags) > 0
    assert result.overall < 5.0


def test_custom_weights_applied() -> None:
    weights = CategoryWeights(fundamentals=0.5, on_chain=0.2, market=0.2, risk=0.1)
    engine = ScoringEngine(weights=weights)
    assert engine.get_weights().fundamentals == 0.5


def test_invalid_weights_raise_error() -> None:
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CategoryWeights(fundamentals=0.5, on_chain=0.5, market=0.5, risk=0.5)


def test_update_weights_at_runtime(sample_altcoin: AltcoinData) -> None:
    engine = ScoringEngine()
    new_weights = CategoryWeights(fundamentals=0.4, on_chain=0.3, market=0.2, risk=0.1)
    engine.update_weights(new_weights)
    result = engine.score(sample_altcoin)
    assert result.overall >= 0


def test_missing_github_data_defaults_to_neutral() -> None:
    data = AltcoinData(
        symbol="NOGH",
        name="No GitHub",
        coingecko_id="nogh",
        market_data=MarketData(
            price_usd=1.0,
            market_cap_usd=1_000_000,
            fully_diluted_valuation_usd=1_000_000,
            volume_24h_usd=100_000,
            price_change_24h_pct=0.0,
            price_change_7d_pct=0.0,
            price_change_30d_pct=0.0,
            all_time_high_usd=2.0,
            ath_change_pct=-50.0,
            circulating_supply=1_000_000,
            liquidity_ratio=0.1,
            fdv_vs_mcap_ratio=1.0,
        ),
        on_chain=OnChainData(github_commits_90d=None),
        fundamentals=FundamentalData(),
    )
    engine = ScoringEngine()
    result = engine.score(data)
    assert 0 <= result.overall <= 10
