# Altcoin Analyzer MCP

> ⚠️ **AVISO**: Esta ferramenta é educacional e não constitui aconselhamento financeiro.
> Criptoativos são altamente voláteis. Faça sua própria pesquisa (DYOR) e consulte um
> profissional qualificado antes de investir.

An MCP (Model Context Protocol) server that provides quantitative scoring and LLM-powered investment analysis for altcoins. Plugs directly into Claude Desktop or any MCP-compatible client.

---

## Architecture

```
altcoin-analyzer-mcp/
├── src/altcoin_analyzer/
│   ├── server.py              # MCP entrypoint (5 tools)
│   ├── config.py              # pydantic-settings (.env)
│   ├── models/                # Pydantic schemas
│   │   ├── altcoin.py         # MarketData, OnChainData, AltcoinData
│   │   ├── scoring.py         # CriterionScore, CategoryScore, ScoringResult
│   │   └── decision.py        # LLMDecision, DecisionOutput
│   ├── providers/             # Async data fetchers
│   │   ├── coingecko.py       # Market data + dev stats
│   │   ├── defillama.py       # TVL history
│   │   └── github_metrics.py  # Commits, stars, contributors
│   ├── scoring/               # Scoring engine
│   │   ├── criteria.py        # 16 scoring criteria across 4 categories
│   │   ├── weights.py         # CategoryWeights (must sum to 1.0)
│   │   └── engine.py          # ScoringEngine
│   ├── llm/                   # Multi-provider LLM client
│   │   ├── client.py          # Anthropic + OpenRouter + OpenAI + fallback
│   │   └── prompts.py         # Decision prompt template
│   ├── tools/                 # MCP tool implementations
│   │   ├── analyze.py         # analyze_altcoin
│   │   ├── compare.py         # compare_altcoins
│   │   ├── score.py           # score_altcoin
│   │   └── _assembler.py      # Data assembly from all providers
│   └── utils/
│       ├── cache.py           # Async TTL cache
│       └── logging.py         # structlog setup
└── tests/                     # pytest suite (≥80% coverage)
```

---

## Installation

### Prerequisites
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### Setup

```bash
git clone <repo>
cd altcoin-analyzer-mcp

# Install with uv
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

---

## Configuration

### API Keys

| Variable | Required | Where to get |
|----------|----------|--------------|
| `ANTHROPIC_API_KEY` | If using Anthropic | [console.anthropic.com](https://console.anthropic.com) |
| `OPENROUTER_API_KEY` | If using OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `OPENAI_API_KEY` | If using OpenAI | [platform.openai.com](https://platform.openai.com) |
| `COINGECKO_API_KEY` | Optional (Pro only) | [coingecko.com/api](https://www.coingecko.com/api) |
| `GITHUB_TOKEN` | Optional (higher rate limits) | [github.com/settings/tokens](https://github.com/settings/tokens) |

### LLM Providers

The server supports three LLM providers with automatic fallback:

```bash
# Primary provider
LLM_PROVIDER=anthropic          # anthropic | openrouter | openai
ANTHROPIC_MODEL=claude-sonnet-4-6

# Fallback (activated if primary fails)
LLM_FALLBACK_PROVIDER=openrouter
LLM_FALLBACK_MODEL=meta-llama/llama-3.1-70b-instruct
OPENROUTER_API_KEY=sk-or-xxx
```

---

## Usage with Claude Desktop

1. Copy `examples/claude_desktop_config.json` to your Claude Desktop config
2. Replace `/absolute/path/to/altcoin-analyzer-mcp` with the actual path
3. Fill in your API keys
4. Restart Claude Desktop

### Example prompts

```
Analise a Solana com perfil de risco moderado e horizonte de médio prazo.
```

```
Compare AVAX, SOL e MATIC para longo prazo.
```

```
Score LINK quickly without LLM reasoning.
```

```
Show me the current scoring criteria and weights.
```

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_altcoin` | Full analysis: scoring + LLM decision (BUY/HOLD/AVOID) |
| `compare_altcoins` | Side-by-side comparison of 2–5 coins with ranking |
| `score_altcoin` | Quantitative score only — fast, no LLM |
| `get_criteria_config` | Returns current criteria, weights, data sources |
| `update_criteria_weights` | Adjust category weights at runtime |

---

## Scoring Framework

Scores range **0–10**. Overall = weighted average of 4 categories.

### Categories & Default Weights

| Category | Weight | Criteria |
|----------|--------|----------|
| **Fundamentals** | 25% | GitHub activity, team transparency, audit status, whitepaper quality |
| **On-Chain** | 25% | Active addresses, transaction volume, holder concentration, TVL growth |
| **Market** | 25% | Liquidity ratio, FDV/MCap, 30d volatility, exchange listings quality |
| **Risk** | 25% | Regulatory jurisdiction, smart contract risk, tokenomics, project age |

Decision thresholds (rule-based when LLM disabled):
- Score ≥ 7.0 → **BUY**
- Score 4.0–7.0 → **HOLD**
- Score ≤ 4.0 → **AVOID**

---

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Start server manually
uv run python -m altcoin_analyzer.server
```

---

## Known Limitations

- Market data depends on CoinGecko free tier (30 req/min limit)
- Fundamental data (audits, team, whitepaper) is partially hardcoded for known coins
- GitHub stats for unknown coins require `github_repo` mapping
- TVL data only available for chains indexed by DeFiLlama

---

## Roadmap

- [ ] Nansen and Glassnode provider integration
- [ ] Persistent scoring history with SQLite
- [ ] Webhook alerts when scores change significantly
- [ ] Portfolio-level analysis across multiple holdings
- [ ] Sentiment analysis via social media APIs

---

## License

MIT
