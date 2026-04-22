# Usage Examples — Altcoin Analyzer MCP

## Prompts for Claude Desktop

### Analyze a single altcoin
```
Analise a Solana com perfil de risco moderado e horizonte de médio prazo.
```

```
Analyze Avalanche (AVAX) with an aggressive risk profile for long-term investment.
```

### Compare multiple altcoins
```
Compare AVAX, SOL e MATIC para longo prazo com perfil moderado.
```

```
Compare ARB, OP, and SOL — which is the best L2/L1 investment right now?
```

### Quick quantitative score (no LLM)
```
Score SOL quickly without LLM reasoning.
```

### Inspect scoring config
```
Show me the current scoring criteria and weights.
```

### Adjust weights at runtime
```
Update the scoring weights: fundamentals=0.35, on_chain=0.30, market=0.20, risk=0.15
```

---

## Direct API examples (Python)

```python
import asyncio
from altcoin_analyzer.tools.analyze import analyze_altcoin
from altcoin_analyzer.tools.compare import compare_altcoins
from altcoin_analyzer.tools.score import score_altcoin

async def main():
    # Full analysis
    result = await analyze_altcoin(
        symbol="SOL",
        include_llm_reasoning=True,
        risk_profile="moderate",
        time_horizon="medium",
    )
    print(result["decision"], result["confidence"])

    # Comparison
    comparison = await compare_altcoins(["SOL", "AVAX", "ARB"])
    for item in comparison["ranking"]:
        print(f"{item['rank']}. {item['symbol']} — score: {item['overall_score']:.2f}")

    # Quick score
    score = await score_altcoin("LINK")
    print(f"LINK overall score: {score['overall']}")

asyncio.run(main())
```
