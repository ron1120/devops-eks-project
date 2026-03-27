# CI/CD plan: Engine + CLI with Jenkins and EKS

## Goal

On every git push:

1. Build and validate engine and CLI artifacts
2. Publish image versions to registry
3. If branch is `main` and checks pass, roll out new engine image to EKS

## Flow

1. Developer pushes code
2. GitHub webhook triggers Jenkins
3. `Jenkinsfile.engine` builds `ghcr.io/ron1120/seyoawe-engine:<tag>`
4. `Jenkinsfile.cli` builds `ghcr.io/ron1120/seyoawe-cli:<tag>`
5. Engine pipeline updates deployment image and waits for rollout success

## Versioning approach

- Shared version source: repository root `VERSION`
- Immutable runtime tag: `<version-from-VERSION>-<git-sha7>`
- Optional moving tag: `latest`
- EKS should always deploy immutable tags for traceability

## Version coupling logic

- Both pipelines resolve the same tag from `VERSION` + commit SHA
- Example: if `VERSION` is `1.0.0` and commit is `abc1234...`, both images become:
	- `ghcr.io/ron1120/seyoawe-engine:1.0.0-abc1234`
	- `ghcr.io/ron1120/seyoawe-cli:1.0.0-abc1234`
- Engine deploy stage includes a coupling gate that waits for the matching CLI tag to exist in the registry before deploying to EKS
- If matching CLI tag is missing, deployment fails and no rollout happens

## Initial cluster bootstrap

Apply Kubernetes manifests once:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/engine-deployment.yaml
kubectl apply -f k8s/engine-service.yaml
kubectl apply -f k8s/engine-hpa.yaml
```

## Rollback command

If a rollout fails after deployment:

```bash
kubectl -n seyoawe rollout undo deployment/seyoawe-engine
```

## Notes

- `docker/Dockerfile.engine` uses `seyoawe.linux`, so builds/deployments target Linux environments.
- CLI image is optional for runtime but useful for automation jobs and reproducible tooling.
- To release a new version family, update `VERSION` in the repo and push.