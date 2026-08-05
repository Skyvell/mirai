FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first (cached layer), then the source.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --frozen --no-dev

# alembic/ rides along (after the install layers — it is not part of the
# package) so the same image serves the API and the migration job.
COPY alembic/ ./alembic/

# Run as non-root.
RUN useradd --create-home --uid 10001 runner && chown -R runner:runner /app
USER runner

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Cloud Run sets $PORT (default 8080).
ENV PORT=8080
CMD ["sh", "-c", "uvicorn mirai_api.main:app --host 0.0.0.0 --port ${PORT}"]
