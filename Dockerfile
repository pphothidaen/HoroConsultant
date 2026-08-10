# syntax=docker/dockerfile:1.7

# Reproducible Linux/AMD64 Rust and ABI3 wheel build.  The release workflow
# selects linux/amd64 explicitly; pinning the image here also makes local builds
# deterministic across Apple Silicon and x86 hosts.
FROM rust:1.97.1-bookworm AS rust-builder

ARG GIT_COMMIT_HASH=unknown

RUN apt-get update \
    && apt-get install --yes --no-install-recommends python3 python3-dev python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/build-venv \
    && /opt/build-venv/bin/python -m pip install --no-cache-dir maturin==1.14.1

WORKDIR /src/rust_core
COPY rust_core/Cargo.toml rust_core/Cargo.lock rust_core/pyproject.toml ./
COPY rust_core/src ./src
COPY rust_core/tests ./tests
COPY rust_core/__init__.py ./__init__.py

RUN GIT_COMMIT_HASH="${GIT_COMMIT_HASH}" cargo build --locked --release --no-default-features --features server --bin horo_server
RUN GIT_COMMIT_HASH="${GIT_COMMIT_HASH}" /opt/build-venv/bin/maturin build --locked --release --out /wheelhouse


FROM python:3.12-slim-bookworm AS runtime

ARG GIT_COMMIT_HASH=unknown
ENV GIT_COMMIT_HASH=${GIT_COMMIT_HASH} \
    HORO_ALLOW_PYTHON_FALLBACK=0 \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
LABEL org.opencontainers.image.title="HoroConsultant" \
      org.opencontainers.image.description="Rust-first Axum gateway with a supervised Python compatibility worker" \
      org.opencontainers.image.source="https://github.com/pphothidaen/HoroConsultant" \
      org.opencontainers.image.revision="${GIT_COMMIT_HASH}" \
      org.opencontainers.image.version="1.0.0"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates curl tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY --from=rust-builder /wheelhouse /tmp/wheelhouse
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --requirement requirements.txt \
    && python -m pip install --no-cache-dir /tmp/wheelhouse/*.whl \
    && rm -rf /tmp/wheelhouse

COPY project ./project
COPY --from=rust-builder /src/rust_core/target/release/horo_server /app/horo_server
RUN chown --recursive appuser:appuser /app \
    && chmod 0555 /app/horo_server

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl --fail --silent --show-error http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/horo_server"]
