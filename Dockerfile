# ---- Builder stage ----
FROM python:3.11-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install .

COPY src/ ./src/

RUN pip install --no-cache-dir --prefix=/install .

# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /build/src/ ./src/
COPY config/ ./config/

RUN chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["python", "-m", "pr_review.cli"]
