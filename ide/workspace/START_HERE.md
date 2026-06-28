# Celaut Service Builder — Start Here

You're in a full **VS Code** running inside a sealed Celaut microVM. Everything
you need to build, configure, and pack a Celaut service is right here — no local
toolchain required.

## 1. Pick a language template

Two ways:

**A. From the VS Code menu (easiest)**
`Terminal → Run Task… → New service from template`, then pick a language and a
name. A ready-to-edit project appears in this workspace.

**B. From the terminal**
```bash
new-service <language> [name]
# e.g.
new-service rust my-solver
```

Available templates:

| Template | Stack |
|---|---|
| `python` | Python 3.11 (slim) |
| `go` | Go 1.22 → distroless/debian-slim |
| `rust` | Rust 1.78 → debian-slim |
| `node-express` | Node 22 (Express) |
| `node-typescript` | Node 22 + TypeScript |
| `java-spring` | Java 21 / Maven (Spring Boot) |
| `java-gradle` | Java 21 / Gradle (Spring Boot) |
| `php-laravel` | PHP 8.3-FPM (Laravel) |

Each template ships a preconfigured **`.service` configuration** —
`Dockerfile`, `service.json`, `pack_config.json`, a `start.sh`, and a copy of
the full configuration guide (`SERVICE_CONFIG_GUIDE.md`).

> The complete reference for every config field lives in
> **[`SERVICE_CONFIG_GUIDE.md`](./SERVICE_CONFIG_GUIDE.md)** in this folder (and
> inside every service you create). Keep it open while editing.

## 2. Edit your service

- Put your code under `src/`.
- Tune `service.json` — entrypoint (`init.entry_path`), API ports, resources,
  and `network` tags.
- The `Dockerfile` only builds a **filesystem** — never define `CMD`,
  `ENTRYPOINT`, or `EXPOSE` (those come from `service.json`). See the guide.

## 3. Pack it into a Celaut service

**From the VS Code menu:** `Terminal → Run Task… → Pack this service`.

**From the terminal:**
```bash
pack-service my-solver
```

This zips the project, sends it to the packer running on `:8080` inside this
same microVM, and writes `<service-id>.celaut.bee` next to your project. The
printed `service-id` is deterministic — packing identical input always yields
the same id.

## What's running here

| Port | What |
|---|---|
| `8080` | The Celaut packer HTTP API (`POST /pack`) |
| `8443` | This VS Code (code-server) |

Both run inside one sealed Cloud-Hypervisor microVM with `network: ["*"]`, so the
nested Docker build can pull base images from any registry.
