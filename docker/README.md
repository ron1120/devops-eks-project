# Engine containerization

This folder provides a minimal Docker setup for running the SeyoAWE engine using the Linux binary (`seyoawe.linux`).

## Files

- `Dockerfile.engine`: builds a Linux container image that runs the engine binary
- `docker-compose.engine.yml`: runs the engine with mounted config/modules/workflows and persistent state

## Build image

Run from repository root:

```bash
docker build -f docker/Dockerfile.engine -t seyoawe/engine:local .
```

## Run with Docker

```bash
docker run --rm -p 8080:8080 -p 8081:8081 \
  -v "$PWD/configuration:/app/configuration" \
  -v "$PWD/modules:/app/modules" \
  -v "$PWD/workflows:/app/workflows" \
  -v "$PWD/seyoawe-community/lifetimes:/app/seyoawe-community/lifetimes" \
  -v "$PWD/seyoawe-community/logs:/app/seyoawe-community/logs" \
  seyoawe/engine:local
```

## Run with Docker Compose

```bash
docker compose -f docker/docker-compose.engine.yml up --build
```

## Notes

- This image currently targets Linux hosts/runners because it uses `seyoawe.linux`.
- Keep `configuration/config.yaml` paths relative to `/app` (current defaults already match this).
- In CI, publish the built image to your container registry and tag it by commit SHA/release version.