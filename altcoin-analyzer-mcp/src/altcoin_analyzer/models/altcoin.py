from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MarketData(BaseModel):
    price_usd: float = Field(ge=0)
    market_cap_usd: float = Field(ge=0)
    fully_diluted_valuation_usd: float = Field(ge=0)
    volume_24h_usd: float = Field(ge=0)
    price_change_24h_pct: float
    price_change_7d_pct: float
    price_change_30d_pct: float
    all_time_high_usd: float = Field(ge=0)
    ath_change_pct: float
    circulating_supply: float = Field(ge=0)
    total_supply: float | None = None
    max_supply: float | None = None
    liquidity_ratio: float = Field(ge=0, description="volume_24h / market_cap")
    fdv_vs_mcap_ratio: float = Field(ge=0, description="fdv / market_cap; 1.0 = fully diluted")

    @field_validator("liquidity_ratio", "fdv_vs_mcap_ratio", mode="before")
    @classmethod
    def clamp_ratio(cls, v: float) -> float:
        return max(0.0, float(v))


class OnChainData(BaseModel):
    tvl_usd: float | None = Field(default=None, ge=0)
    tvl_change_7d_pct: float | None = None
    tvl_change_30d_pct: float | None = None
    active_addresses_7d: int | None = Field(default=None, ge=0)
    transaction_count_24h: int | None = Field(default=None, ge=0)
    github_commits_90d: int | None = Field(default=None, ge=0)
    github_stars: int | None = Field(default=None, ge=0)
    github_contributors: int | None = Field(default=None, ge=0)
    github_repo: str | None = None


class FundamentalData(BaseModel):
    audit_firms: list[str] = Field(default_factory=list)
    is_audited: bool = False
    team_known: bool = False
    has_whitepaper: bool = False
    whitepaper_quality_score: float = Field(default=5.0, ge=0, le=10)
    regulatory_jurisdiction: str | None = None
    project_inception_year: int | None = None
    exchange_listings: list[str] = Field(default_factory=list)


class AltcoinData(BaseModel):
    symbol: str
    name: str
    coingecko_id: str
    market_data: MarketData
    on_chain: OnChainData
    fundamentals: FundamentalData
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    data_gaps: list[str] = Field(default_factory=list, description="Fields that could not be fetched")
