"""
MCP Server entrypoint — Altcoin Analyzer.

Exposes 5 tools via the Model Context Protocol:
  1. analyze_altcoin
  2. compare_altcoins
  3. score_altcoin
  4. get_criteria_config
  5. update_criteria_weights
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from altcoin_analyzer.config import settings
from altcoin_analyzer.scoring.criteria import CRITERIA_CONFIG
from altcoin_analyzer.scoring.engine import ScoringEngine
from altcoin_analyzer.scoring.weights import CategoryWeights
from altcoin_analyzer.tools.analyze import analyze_altcoin
from altcoin_analyzer.tools.compare import compare_altcoins
from altcoin_analyzer.tools.score import score_altcoin
from altcoin_analyzer.utils.logging import get_logger, setup_logging

setup_logging(settings.log_level)
logger = get_logger(__name__)

app = Server("altcoin-analyzer")
_scoring_engine = ScoringEngine()


# ─── Tool Definitions ────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="analyze_altcoin",
            description=(
                "Full analysis of an altcoin: fetches on-chain + market data, "
                "computes quantitative scores and calls an LLM (Claude/GPT/OpenRouter) "
                "for a structured BUY / HOLD / AVOID recommendation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol, e.g. SOL, AVAX"},
                    "include_llm_reasoning": {"type": "boolean", "default": True},
                    "risk_profile": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"],
                        "default": "moderate",
                    },
                    "time_horizon": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "default": "medium",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="compare_altcoins",
            description="Compare 2–5 altcoins side-by-side with quantitative scoring and ranking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 5,
                        "description": "List of ticker symbols, e.g. [\"SOL\", \"AVAX\", \"ARB\"]",
                    },
                    "risk_profile": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"],
                        "default": "moderate",
                    },
                },
                "required": ["symbols"],
            },
        ),
        Tool(
            name="score_altcoin",
            description="Quantitative scoring only (no LLM). Fast screening of a single altcoin.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol, e.g. LINK"},
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_criteria_config",
            description="Returns the current scoring criteria, weights, and data sources for transparency.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="update_criteria_weights",
            description=(
                "Adjust the category weights at runtime. "
                "Values must be between 0 and 1 and sum to exactly 1.0."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fundamentals": {"type": "number", "minimum": 0, "maximum": 1},
                    "on_chain": {"type": "number", "minimum": 0, "maximum": 1},
                    "market": {"type": "number", "minimum": 0, "maximum": 1},
                    "risk": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["fundamentals", "on_chain", "market", "risk"],
            },
        ),
    ]


# ─── Tool Dispatcher ─────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    logger.info("tool_called", tool=name, arguments=list(arguments.keys()))

    try:
        result = await _dispatch(name, arguments)
    except Exception as exc:
        logger.error("tool_error", tool=name, error=str(exc), exc_info=True)
        result = {"error": str(exc), "tool": name}

    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


async def _dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "analyze_altcoin":
        return await analyze_altcoin(
            symbol=args["symbol"],
            include_llm_reasoning=args.get("include_llm_reasoning", True),
            risk_profile=args.get("risk_profile", "moderate"),  # type: ignore[arg-type]
            time_horizon=args.get("time_horizon", "medium"),  # type: ignore[arg-type]
        )

    if name == "compare_altcoins":
        return await compare_altcoins(
            symbols=args["symbols"],
            risk_profile=args.get("risk_profile", "moderate"),  # type: ignore[arg-type]
        )

    if name == "score_altcoin":
        return await score_altcoin(symbol=args["symbol"])

    if name == "get_criteria_config":
        return _get_criteria_config()

    if name == "update_criteria_weights":
        return _update_weights(args)

    return {"error": f"Unknown tool: {name}"}


def _get_criteria_config() -> dict[str, Any]:
    config: dict[str, Any] = {"categories": {}, "current_weights": _scoring_engine.get_weights().model_dump()}
    for cat, cfg in CRITERIA_CONFIG.items():
        config["categories"][cat] = [
            {"name": name, "weight": weight, "source": source}
            for name, weight, source, _ in cfg["criteria"]
        ]
    return config


def _update_weights(args: dict[str, Any]) -> dict[str, Any]:
    try:
        new_weights = CategoryWeights(
            fundamentals=float(args["fundamentals"]),
            on_chain=float(args["on_chain"]),
            market=float(args["market"]),
            risk=float(args["risk"]),
        )
    except Exception as e:
        return {"error": str(e)}

    _scoring_engine.update_weights(new_weights)
    logger.info("weights_updated", **new_weights.model_dump())
    return {"success": True, "new_weights": new_weights.model_dump()}


# ─── Entrypoint ──────────────────────────────────────────────────────────────

async def _main() -> None:
    logger.info("server_starting", provider=settings.llm_provider, fallback=settings.llm_fallback_provider or "none")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    run()
