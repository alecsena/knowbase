import pytest

from altcoin_analyzer.models.altcoin import AltcoinData, FundamentalData, MarketData, OnChainData


@pytest.fixture
def sample_market_data() -> MarketData:
    return MarketData(
        price_usd=150.0,
        market_cap_usd=70_000_000_000,
        fully_diluted_valuation_usd=80_000_000_000,
        volume_24h_usd=3_500_000_000,
        price_change_24h_pct=2.5,
        price_change_7d_pct=5.0,
        price_change_30d_pct=15.0,
        all_time_high_usd=260.0,
        ath_change_pct=-42.0,
        circulating_supply=460_000_000,
        total_supply=580_000_000,
        max_supply=None,
        liquidity_ratio=0.05,
        fdv_vs_mcap_ratio=1.14,
    )


@pytest.fixture
def sample_on_chain() -> OnChainData:
    return OnChainData(
        tvl_usd=5_000_000_000,
        tvl_change_7d_pct=3.0,
        tvl_change_30d_pct=12.0,
        active_addresses_7d=500_000,
        transaction_count_24h=10_000_000,
        github_commits_90d=300,
        github_stars=12_000,
        github_contributors=150,
        github_repo="solana-labs/solana",
    )


@pytest.fixture
def sample_fundamentals() -> FundamentalData:
    return FundamentalData(
        audit_firms=["Kudelski", "Neodyme"],
        is_audited=True,
        team_known=True,
        has_whitepaper=True,
        whitepaper_quality_score=8.5,
        regulatory_jurisdiction="USA",
        project_inception_year=2020,
        exchange_listings=["binance", "coinbase", "kraken", "bybit", "okx"],
    )


@pytest.fixture
def sample_altcoin(sample_market_data: MarketData, sample_on_chain: OnChainData, sample_fundamentals: FundamentalData) -> AltcoinData:
    return AltcoinData(
        symbol="SOL",
        name="Solana",
        coingecko_id="solana",
        market_data=sample_market_data,
        on_chain=sample_on_chain,
        fundamentals=sample_fundamentals,
    )


@pytest.fixture
def coingecko_response() -> dict:
    return {
        "id": "solana",
        "symbol": "sol",
        "name": "Solana",
        "market_data": {
            "current_price": {"usd": 150.0},
            "market_cap": {"usd": 70_000_000_000},
            "fully_diluted_valuation": {"usd": 80_000_000_000},
            "total_volume": {"usd": 3_500_000_000},
            "price_change_percentage_24h": 2.5,
            "price_change_percentage_7d": 5.0,
            "price_change_percentage_30d": 15.0,
            "ath": {"usd": 260.0},
            "ath_change_percentage": {"usd": -42.0},
            "circulating_supply": 460_000_000,
            "total_supply": 580_000_000,
            "max_supply": None,
        },
        "developer_data": {
            "commit_count_4_weeks": 100,
            "stars": 12000,
            "pull_request_contributors": 150,
        },
    }


@pytest.fixture
def defillama_response() -> list:
    base = 5_000_000_000
    return [{"date": i, "tvl": base + i * 10_000_000} for i in range(35)]


LLM_DECISION_JSON = """{
  "decision": "BUY",
  "confidence": 0.78,
  "reasoning": "Solana apresenta métricas sólidas com TVL de $5B e crescimento de 12% em 30 dias.",
  "key_risks": ["Alta volatilidade histórica", "Dependência de validators"],
  "key_opportunities": ["Ecosystem DeFi crescendo", "Alta velocidade de transações"],
  "suggested_allocation_pct": 5,
  "stop_loss_suggestion_pct": 15,
  "reevaluation_trigger": "Queda de TVL acima de 20% ou incidente de rede"
}"""
