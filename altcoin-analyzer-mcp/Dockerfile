# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (layer-cache friendly)
COPY pyproject.toml uv.lock ./

# Install only production deps into a fixed location
RUN uv sync --no-dev --frozen --no-editable

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy the virtual-env produced by uv (includes the installed package)
COPY --from=builder /app/.venv /app/.venv

# Copy source only
COPY src/ ./src/
COPY pyproject.toml ./

# Install the package itself (no deps, already present in .venv)
RUN /app/.venv/bin/pip install --no-deps -e . --quiet

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

# MCP stdio server — invoked by the MCP client (Claude Desktop, etc.)
# The container is expected to be run with -i so stdin is attached.
ENTRYPOINT ["python", "-m", "altcoin_analyzer.server"]
