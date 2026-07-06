FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

ENV UV_HTTP_TIMEOUT=300

COPY services/stream_judge/pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r pyproject.toml

COPY shared/ ./shared/
COPY services/stream_judge/ ./

EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
