# syntax=docker/dockerfile:1

FROM python:3.14-slim AS builder
RUN pip install --no-cache-dir uv
WORKDIR /build
ARG APP_VERSION=0.1.0
COPY pyproject.toml uv.lock ./
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --no-install-project --no-cache
COPY pihole_exporter/ ./pihole_exporter/

FROM python:3.14-slim
COPY --from=builder /build/.venv /app/.venv
WORKDIR /workspace
COPY --from=builder /build/pihole_exporter /workspace/pihole_exporter
ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"
LABEL org.opencontainers.image.source="https://github.com/cdelgehier/pihole-exporter"
LABEL org.opencontainers.image.description="Prometheus exporter for Pi-hole v6"
LABEL org.opencontainers.image.licenses="MIT"
ENTRYPOINT ["python", "-m", "pihole_exporter.main"]
