# Jenkins pipelines for engine and CLI

This folder contains two independent pipelines:

- `Jenkinsfile.engine`: builds/tests/pushes engine image and deploys to EKS on `main`
- `Jenkinsfile.cli`: validates CLI and publishes a CLI container image

## Required Jenkins credentials

- `ghcr-creds`: username/password or PAT credentials for container registry push
- `kubeconfig-eks`: file credential with kubeconfig for your EKS cluster

## Recommended Jenkins jobs

- `seyoawe-engine-pipeline` -> Pipeline from SCM, script path `jenkins/Jenkinsfile.engine`
- `seyoawe-cli-pipeline` -> Pipeline from SCM, script path `jenkins/Jenkinsfile.cli`

## Trigger model

- GitHub webhook on push
- Pipelines run per push
- Engine deploy stage runs only for branch `main`

## Version coupling

- Single source of truth: root `VERSION` file
- Both pipelines compute image tags as `<VERSION>-<git-sha7>`
- Engine pipeline blocks deployment unless matching CLI tag exists in registry
- This ensures engine and CLI for a rollout are from the same version family and commit
