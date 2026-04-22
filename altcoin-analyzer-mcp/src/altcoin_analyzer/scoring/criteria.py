"""
Scoring criteria definitions.

Each criterion is a callable (altcoin_data: AltcoinData) -> (score: float, note: str).
Score range: 0-10.
"""

from collections.abc import Callable

from altcoin_analyzer.models.altcoin import AltcoinData

CriterionFn = Callable[[AltcoinData], tuple[float, str]]


def _clamp(v: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, v))


# ─── Fundamentals ────────────────────────────────────────────────────────────

def github_activity(data: AltcoinData) -> tuple[float, str]:
    commits = data.on_chain.github_commits_90d
    if commits is None:
        return 5.0, "no data"
    score = _clamp(commits / 30)  # 300 commits = 10
    return score, f"{commits} commits in 90d"


def team_transparency(data: AltcoinData) -> tuple[float, str]:
    score = 10.0 if data.fundamentals.team_known else 3.0
    return score, "team known" if data.fundamentals.team_known else "anonymous team"


def audit_status(data: AltcoinData) -> tuple[float, str]:
    if data.fundamentals.is_audited:
        firms = ", ".join(data.fundamentals.audit_firms) or "unknown firm"
        return 9.0, f"audited by {firms}"
    return 2.0, "no audit found"


def whitepaper_quality(data: AltcoinData) -> tuple[float, str]:
    if not data.fundamentals.has_whitepaper:
        return 1.0, "no whitepaper"
    score = _clamp(data.fundamentals.whitepaper_quality_score)
    return score, f"quality score {score:.1f}"


# ─── On-Chain ────────────────────────────────────────────────────────────────

def active_addresses_growth(data: AltcoinData) -> tuple[float, str]:
    addrs = data.on_chain.active_addresses_7d
    if addrs is None:
        return 5.0, "no data"
    score = _clamp(addrs / 10_000)  # 100k = 10
    return score, f"{addrs:,} active addresses (7d)"


def transaction_volume(data: AltcoinData) -> tuple[float, str]:
    vol = data.market_data.volume_24h_usd
    if vol == 0:
        return 0.0, "zero volume"
    score = _clamp(vol / 100_000_000)  # $1B = 10
    return score, f"${vol:,.0f} daily volume"


def holder_concentration(data: AltcoinData) -> tuple[float, str]:
    # Proxy: FDV/MCap ratio — high ratio implies insider/whale concentration
    fdv_ratio = data.market_data.fdv_vs_mcap_ratio
    if fdv_ratio >= 3.0:
        return 2.0, f"high concentration risk (FDV/MCap={fdv_ratio:.1f}x)"
    if fdv_ratio >= 1.5:
        return 5.0, f"moderate concentration (FDV/MCap={fdv_ratio:.1f}x)"
    return 8.0, f"low concentration risk (FDV/MCap={fdv_ratio:.1f}x)"


def tvl_growth(data: AltcoinData) -> tuple[float, str]:
    change = data.on_chain.tvl_change_30d_pct
    tvl = data.on_chain.tvl_usd
    if tvl is None or tvl == 0:
        return 5.0, "no TVL data (non-DeFi chain or data unavailable)"
    if change is None:
        return 5.0, f"TVL=${tvl:,.0f}, change unknown"
    score = _clamp(5.0 + change / 10)  # +100% => 15 clamped to 10; -50% => 0
    return score, f"TVL=${tvl:,.0f}, 30d change={change:.1f}%"


# ─── Market ──────────────────────────────────────────────────────────────────

def liquidity_ratio(data: AltcoinData) -> tuple[float, str]:
    lr = data.market_data.liquidity_ratio
    score = _clamp(lr * 100)  # 10% ratio = 10
    return score, f"liquidity ratio {lr*100:.2f}%"


def fdv_vs_mcap(data: AltcoinData) -> tuple[float, str]:
    ratio = data.market_data.fdv_vs_mcap_ratio
    if ratio >= 5.0:
        return 1.0, f"FDV/MCap={ratio:.1f}x — massive inflation risk"
    if ratio >= 2.0:
        return 4.0, f"FDV/MCap={ratio:.1f}x — high inflation risk"
    if ratio >= 1.2:
        return 7.0, f"FDV/MCap={ratio:.1f}x — moderate inflation risk"
    return 9.0, f"FDV/MCap={ratio:.1f}x — low inflation risk"


def price_volatility_30d(data: AltcoinData) -> tuple[float, str]:
    change = abs(data.market_data.price_change_30d_pct)
    if change > 80:
        return 2.0, f"extreme 30d volatility: {data.market_data.price_change_30d_pct:.1f}%"
    if change > 40:
        return 5.0, f"high 30d volatility: {data.market_data.price_change_30d_pct:.1f}%"
    if change > 20:
        return 7.0, f"moderate 30d volatility: {data.market_data.price_change_30d_pct:.1f}%"
    return 9.0, f"low 30d volatility: {data.market_data.price_change_30d_pct:.1f}%"


def exchange_listings_quality(data: AltcoinData) -> tuple[float, str]:
    listings = data.fundamentals.exchange_listings
    tier1 = {"binance", "coinbase", "kraken", "bybit", "okx", "upbit"}
    tier1_count = sum(1 for e in listings if e.lower() in tier1)
    score = _clamp(tier1_count * 2.5)
    return score, f"{tier1_count} tier-1 exchange listings"


# ─── Risk ────────────────────────────────────────────────────────────────────

def regulatory_jurisdiction(data: AltcoinData) -> tuple[float, str]:
    jur = (data.fundamentals.regulatory_jurisdiction or "").lower()
    high_risk = {"china", "iran", "north korea", "russia"}
    low_risk = {"usa", "eu", "uk", "singapore", "switzerland", "cayman islands", "british virgin islands"}
    if any(h in jur for h in high_risk):
        return 2.0, f"high-risk jurisdiction: {jur}"
    if any(loc in jur for loc in low_risk):
        return 8.0, f"favorable jurisdiction: {jur}"
    if not jur:
        return 5.0, "jurisdiction unknown"
    return 5.0, f"jurisdiction: {jur}"


def smart_contract_risk(data: AltcoinData) -> tuple[float, str]:
    # Proxy: is_audited + audit firms
    if data.fundamentals.is_audited and data.fundamentals.audit_firms:
        return 8.0, "audited smart contracts"
    if data.fundamentals.is_audited:
        return 6.0, "audited (firm unknown)"
    return 3.0, "unaudited smart contracts"


def tokenomics_distribution(data: AltcoinData) -> tuple[float, str]:
    fdv_ratio = data.market_data.fdv_vs_mcap_ratio
    if fdv_ratio > 3:
        return 2.0, f"poor tokenomics (FDV/MCap={fdv_ratio:.1f}x)"
    if fdv_ratio > 1.5:
        return 5.0, f"moderate tokenomics (FDV/MCap={fdv_ratio:.1f}x)"
    return 8.0, f"healthy tokenomics (FDV/MCap={fdv_ratio:.1f}x)"


def age_of_project(data: AltcoinData) -> tuple[float, str]:
    from datetime import datetime

    inception = data.fundamentals.project_inception_year
    if inception is None:
        return 5.0, "inception year unknown"
    age = datetime.utcnow().year - inception
    score = _clamp(age * 1.5)  # 6+ years = 9+
    return score, f"project age: {age} year(s)"


# ─── Registry ────────────────────────────────────────────────────────────────

CRITERIA_CONFIG: dict[str, dict[str, list[tuple[str, float, str, CriterionFn]]]] = {
    "fundamentals": {
        "criteria": [
            ("github_activity", 0.30, "github", github_activity),
            ("team_transparency", 0.25, "manual", team_transparency),
            ("audit_status", 0.25, "manual", audit_status),
            ("whitepaper_quality", 0.20, "manual", whitepaper_quality),
        ]
    },
    "on_chain": {
        "criteria": [
            ("active_addresses_growth", 0.30, "defillama/glassnode", active_addresses_growth),
            ("transaction_volume", 0.25, "coingecko", transaction_volume),
            ("holder_concentration", 0.25, "coingecko", holder_concentration),
            ("tvl_growth", 0.20, "defillama", tvl_growth),
        ]
    },
    "market": {
        "criteria": [
            ("liquidity_ratio", 0.30, "coingecko", liquidity_ratio),
            ("fdv_vs_mcap", 0.25, "coingecko", fdv_vs_mcap),
            ("price_volatility_30d", 0.25, "coingecko", price_volatility_30d),
            ("exchange_listings_quality", 0.20, "manual", exchange_listings_quality),
        ]
    },
    "risk": {
        "criteria": [
            ("regulatory_jurisdiction", 0.30, "manual", regulatory_jurisdiction),
            ("smart_contract_risk", 0.25, "manual", smart_contract_risk),
            ("tokenomics_distribution", 0.25, "coingecko", tokenomics_distribution),
            ("age_of_project", 0.20, "manual", age_of_project),
        ]
    },
}
