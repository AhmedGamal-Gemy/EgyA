FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

ENV UV_HTTP_TIMEOUT=300


COPY services/report_agent/pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r pyproject.toml

COPY shared/ ./shared/
COPY services/report_agent/ ./

EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
