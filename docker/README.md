# Docker Images

Multi-stage Dockerfiles for the **engine** and **CLI**: tests run in the first stage, runtime image in the second. Jenkins (`Jenkinsfile.cli`, `Jenkinsfile.engine`) builds from the **repo root** as context.

---

## Files

| File                                               | Image                                                                                                   |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| [`Dockerfile.cli`](Dockerfile.cli)                 | `sawectl` — Python entrypoint + packaged `cli/binaries/linux/sawectl`.                                  |
| [`Dockerfile.engine`](Dockerfile.engine)           | Automation engine — `seyoawe.linux` binary, `VOLUME /app/seyoawe-community`, port `8080`.               |
| [`Dockerfile.cli_test`](Dockerfile.cli_test)       | CLI tests only (local / ad-hoc; CI uses the `test` stage in `Dockerfile.cli`).                          |
| [`Dockerfile.engine_test`](Dockerfile.engine_test) | Engine tests only (same idea).                                                                          |

---

## Build (from repo root)

```bash
docker build -f docker/Dockerfile.cli    --target production -t sawe-cli:local    .
docker build -f docker/Dockerfile.engine --target production -t sawe-engine:local .
```

Jenkins passes `--build-arg VERSION=$(cat VERSION)`; the production stage records it as `org.opencontainers.image.version`.

---

## Test stages

```bash
docker build -f docker/Dockerfile.cli    --target test -t sawe-cli:test    .
docker build -f docker/Dockerfile.engine --target test -t sawe-engine:test .
```

---

## Context

Builds use `.` (repo root) as context. The root [`.dockerignore`](../.dockerignore) excludes virtualenvs, `.git`, Terraform state, and anything not `COPY`'d — keeping local and CI builds fast.
