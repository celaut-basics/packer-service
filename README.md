# celaut-packer-service

A Celaut microVM service that **does the same thing `nodo pack` does**, exposed
over HTTP. Give it a project archive (a zip with a `Dockerfile`, a
`pack_config.json` and a `service.json`); it builds the image, exports the
filesystem, serialises a content-addressed `celaut.Service`, and returns the
packed service as a single **`.celaut.bee`** file.

It is a thin wrapper around the *real* nodo packer
([`src/packers/zip_with_dockerfile.py`](https://github.com/celaut-project/nodo/tree/stable/src/packers)),
vendored into the image — not a re-implementation — so the `service_id` it emits
is byte-identical to `nodo pack`.

## API

Bound on `0.0.0.0:8080` (declared in `service.json`).

| Method | Path      | Body                | Response |
|--------|-----------|---------------------|----------|
| GET    | `/health` | —                   | `200 ok` |
| POST   | `/pack`   | project `.zip`      | `200` → `application/octet-stream` (`.celaut.bee`); header `X-Service-Id: <hex>`; `Content-Disposition: attachment; filename="<id>.celaut.bee"` |

Errors: `415` (not a zip), `400` (missing `service.json`/`Dockerfile`, or a
packer/validation error with the message in the body), `413` (too large), `500`
(unexpected).

The zip must contain, at its root **or** inside a single top-level folder:
`Dockerfile`, `service.json`, and optionally `pack_config.json`.

### Example

```bash
# zip a project (the same layout nodo pack expects)
( cd examples/hello && zip -r - . ) > /tmp/hello.zip

# pack it via the running service
curl -sS -X POST --data-binary @/tmp/hello.zip \
     -H 'Content-Type: application/zip' \
     -D /tmp/headers.txt -o /tmp/hello.celaut.bee \
     http://<service-ip>:8080/pack

grep -i x-service-id /tmp/headers.txt   # the content-addressed id
```

## How it works (architecture)

```
POST /pack (zip)
   │
   ▼
server.py  ── unzip, validate (service.json + Dockerfile) ──┐
   │                                                        │
   ▼                                                        │
nodo worker:  python -m src.packers.zip_with_dockerfile     │  in-VM dockerd
   │  docker buildx build --output type=tar  ───────────────┘  (docker-in-docker)
   │  → export rootfs → walk fs → build celaut.Service protobuf
   │  → multiblock dir + content hash = service_id
   ▼
bee_rpc.read_multiblock_directory(service_dir) → bytes  →  <id>.celaut.bee
```

`start.sh` boots an in-VM Docker daemon (DinD) and a host-network `buildx`
builder, then runs `server.py`. **This is why the service declares
`network: tag=(*)`** — buildx must reach arbitrary container registries to pull
the base images referenced by the Dockerfile being packed.

## Bootstrap / dogfood test

The acceptance test from the brief is a two-step bootstrap:

1. **Pack the packer with the node.** On the amd64 node (Alienware WSL2):
   `nodo pack workspace/celaut-packer-service` → `celaut-packer-service` gets a
   real service-id; `nodo execute` it to get a running instance with an IP.
2. **Pack another service with the packer.** Zip e.g. `examples/hello` (or
   `celaut-sat-solver`) and `POST /pack` it to the running packer instance. The
   returned `.celaut.bee` / `X-Service-Id` must match what `nodo pack` produces
   for the same project. `nodo import <id>.celaut.bee` should accept it.

## Status & the one open risk

- Scaffold complete; `server.py` HTTP/zip layer is unit-tested locally.
- **End-to-end (build + real `.bee` + dogfood) can only run on an amd64 + KVM
  node** — this Mac is aarch64 with no KVM. That validation runs on Alienware.
- **Open risk:** whether a cloud-hypervisor microVM permits a nested Docker
  daemon (DinD needs privileged/overlay/iptables). If Celaut's runtime forbids
  it, the fix is localised to `start.sh` + `Dockerfile` — swap DinD for talking
  to the host nodo's dockerd socket — while `server.py` and the packing contract
  stay the same.
- The Python dep set in the `Dockerfile` (bee_rpc + nodo requirements) is the
  other spot that may need a pin tweak on the first real amd64 build.
