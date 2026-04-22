import json
from typing import Any

DECISION_PROMPT = """\
Você é um analista senior de criptoativos com 10+ anos de experiência.

Analise os dados abaixo da altcoin **{symbol}** e forneça uma recomendação de investimento.

## Perfil do Investidor
- Risco: {risk_profile}
- Horizonte: {time_horizon}

## Scores Quantitativos (0-10)
{scores_json}

## Dados de Mercado
{market_data_json}

## Métricas On-Chain
{onchain_data_json}

## Red Flags Detectados
{red_flags}

## Green Flags Detectados
{green_flags}

---

Forneça sua análise em JSON estrito com a seguinte estrutura:

{{
  "decision": "BUY | HOLD | AVOID",
  "confidence": 0.0,
  "reasoning": "Análise detalhada em 3-5 parágrafos",
  "key_risks": ["risco1", "risco2"],
  "key_opportunities": ["oportunidade1"],
  "suggested_allocation_pct": 0,
  "stop_loss_suggestion_pct": 10,
  "reevaluation_trigger": "Condição que deve disparar nova análise"
}}

Regras:
- "decision" deve ser exatamente "BUY", "HOLD" ou "AVOID"
- "confidence" entre 0.0 e 1.0
- "suggested_allocation_pct" entre 0 e 10
- "stop_loss_suggestion_pct" entre 5 e 30
- Seja objetivo, cite os dados específicos que embasam cada conclusão
- NÃO invente dados. Se informação estiver faltando, mencione explicitamente
- Retorne APENAS o JSON, sem markdown ou texto adicional\
"""


def build_decision_prompt(
    symbol: str,
    risk_profile: str,
    time_horizon: str,
    scores: dict[str, float],
    market_data: dict[str, Any],
    onchain_data: dict[str, Any],
    red_flags: list[str],
    green_flags: list[str],
) -> str:
    return DECISION_PROMPT.format(
        symbol=symbol,
        risk_profile=risk_profile,
        time_horizon=time_horizon,
        scores_json=json.dumps(scores, indent=2, ensure_ascii=False),
        market_data_json=json.dumps(market_data, indent=2, ensure_ascii=False),
        onchain_data_json=json.dumps(onchain_data, indent=2, ensure_ascii=False),
        red_flags="\n".join(f"- {f}" for f in red_flags) or "Nenhum",
        green_flags="\n".join(f"- {f}" for f in green_flags) or "Nenhum",
    )
