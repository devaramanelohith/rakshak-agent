FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PORT=8080
WORKDIR /srv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra gcp --no-install-project
COPY app ./app
COPY web ./web
COPY data ./data
COPY sql ./sql
COPY scripts ./scripts
EXPOSE 8080
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--ws", "websockets", "--timeout-keep-alive", "75"]
