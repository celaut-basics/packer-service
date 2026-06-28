#!/bin/sh
# Celaut init entrypoint for the packer service (declared in service.json ->
# init.entry_path). The microVM init runs this; Docker CMD/ENTRYPOINT are ignored
# by the packer that builds THIS image.
#
# Sequence:
#   1. Boot an in-VM Docker daemon (docker-in-docker) + a host-network buildx
#      builder — the nodo packer shells out to `docker buildx build`.
#   2. Export the env the nodo ConfigManager / packer expect.
#   3. Launch the HTTP packer front-end on 0.0.0.0:8080.
set -e

export CACHE="${CACHE:-/var/lib/celaut/cache/}"
export BLOCKDIR="${BLOCKDIR:-/var/lib/celaut/blocks/}"
export NODO_DIR="${NODO_DIR:-/opt/nodo}"
# Packer tunables consumed by ConfigManager (safe defaults mirroring nodo).
export PACKER_MEMORY_SIZE_FACTOR="${PACKER_MEMORY_SIZE_FACTOR:-2}"
export MIN_BUFFER_BLOCK_SIZE="${MIN_BUFFER_BLOCK_SIZE:-1048576}"
export SAVE_ALL="${SAVE_ALL:-False}"
export MAIN_DIR="${NODO_DIR}"
export PYTHONPATH="${NODO_DIR}:${PYTHONPATH}"
# Build with the host-network builder so buildx egress uses the VM's (*) channel.
export BUILDX_BUILDER="${BUILDX_BUILDER:-nodo-hostnet}"

mkdir -p "$CACHE" "$BLOCKDIR"

echo "[start] booting in-VM dockerd..."
# docker:dind ships dockerd-entrypoint.sh which sets up storage + iptables.
dockerd-entrypoint.sh dockerd >/var/log/dockerd.log 2>&1 &

# Wait for the daemon socket to come up before packing.
tries=0
until docker info >/dev/null 2>&1; do
  tries=$((tries + 1))
  if [ "$tries" -gt 120 ]; then
    echo "[start] dockerd did not become ready in time; last log:" >&2
    tail -n 40 /var/log/dockerd.log >&2 || true
    exit 1
  fi
  sleep 1
done
echo "[start] dockerd ready."

# Host-network buildx builder (matches nodo's packer.docker.BUILDX_BUILDER).
if ! docker buildx inspect "$BUILDX_BUILDER" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDX_BUILDER" \
    --driver docker-container --driver-opt network=host >/dev/null 2>&1 || true
fi
docker buildx inspect "$BUILDX_BUILDER" --bootstrap >/dev/null 2>&1 || true

echo "[start] launching packer HTTP server on :8080"
exec python3 /app/server.py
