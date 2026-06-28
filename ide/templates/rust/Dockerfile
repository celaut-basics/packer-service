# Rust service. Dependency layer is built first for caching, then the source.
FROM rust:1.78-slim AS builder
WORKDIR /build
COPY ./Cargo.toml ./Cargo.toml
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release && rm -rf src
COPY ./src ./src
RUN touch src/main.rs && cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /build/target/release/myservice /app/myservice
COPY ./start.sh /app/start.sh
RUN chmod +x /app/myservice /app/start.sh
