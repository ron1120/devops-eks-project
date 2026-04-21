# Docker images

Production images are multi-stage: **run tests in the first stage**, then build the runtime image. Jenkins (`Jenkinsfile.cli`, `Jenkinsfile.engine`) builds from the **repository root** as context.

| File | Image purpose |
|------|-----------------|
| [`Dockerfile.cli`](Dockerfile.cli) | `sawectl` — Python entrypoint + packaged `cli/binaries/linux/sawectl`. |
| [`Dockerfile.engine`](Dockerfile.engine) | Automation engine — `seyoawe.linux` binary, `VOLUME /app/seyoawe-community`, port `8080`. |
| [`Dockerfile.cli_test`](Dockerfile.cli_test) | CLI tests only (used for local or ad-hoc runs; CI uses the test stage in `Dockerfile.cli`). |
| [`Dockerfile.engine_test`](Dockerfile.engine_test) | Engine tests only (same idea). |

## Build (from repo root)

```bash
# CLI (production stage is default final stage)
docker build -f docker/Dockerfile.cli --target production -t sawe-cli:local .

# Engine
docker build -f docker/Dockerfile.engine --target production -t sawe-engine:local .
```

Jenkins passes `--build-arg VERSION=$(cat VERSION)`; the production stage records it as `org.opencontainers.image.version`.

## Test stages

```bash
docker build -f docker/Dockerfile.cli --target test -t sawe-cli:test .
docker build -f docker/Dockerfile.engine --target test -t sawe-engine:test .
```

## Context and `.dockerignore`

Builds use `.` as context. A root [`.dockerignore`](../.dockerignore) excludes virtualenvs, `.git`, Terraform state, and paths not `COPY`’d into images so local and CI builds stay smaller and faster.
