FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

ENV UV_HTTP_TIMEOUT=300

COPY services/setup_agent/pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r pyproject.toml

COPY shared/ ./shared/
COPY services/setup_agent/ ./

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
