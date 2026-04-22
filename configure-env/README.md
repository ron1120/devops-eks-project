# configure-env

Local environment file for this repo: **Jenkins host IP** (Ansible), **Docker Hub / GitHub** values synced to **AWS Secrets Manager**, and optional **AWS access keys** for documentation or local tooling.

`.env` is gitignored. Copy the example and fill in values:

```bash
cp .env.example .env
```

## Variables (see `.env.example`)

| Variable | Purpose |
|----------|---------|
| `AWS_REGION` | AWS region (e.g. `us-east-1`) for CLI and Secrets Manager calls. |
| `JENKINS_EIP` | Elastic IP of the Jenkins EC2 host. Used by `ansible/inventory.sh` when you run playbooks. |
| `DOCKERHUB_USERNAME` / `DOCKERHUB_PASSWORD` | Docker Hub credentials pushed to Secrets Manager by `export-env.sh`. |
| `AWS_DOCKERHUB_SECRET_ID` | Secrets Manager secret name for Docker Hub (e.g. `DockerHubCredentials`). |
| `GIT_USERNAME` / `GIT_API_TOKEN` | GitHub user and PAT for Jenkins **Tag Release** (`jenkins/Jenkinsfile.cli`); pushed by `export-env.sh`. |
| `AWS_GIT_SECRET_ID` | Secrets Manager secret name for GitHub (e.g. `RonGitUser`). |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Optional. If unset, the AWS CLI uses your usual provider chain (`~/.aws/credentials`, `AWS_PROFILE`, SSO, etc.). You can set these in `.env` or only on your shell. |
| `AWS_PROFILE` | Optional, when you are not using static keys. |

## Sync secrets to AWS

[`export-env.sh`](export-env.sh) loads `.env` and calls `put-secret-value` for Docker Hub and GitHub. Your AWS identity must be allowed to update those secrets (same as running the `aws` commands yourself).

```bash
cd configure-env
./export-env.sh
```

If `aws` fails, fix credentials outside this script (e.g. `aws configure`, valid keys, or `aws sso login`).

### `InvalidSignatureException` / “signature we calculated does not match”

That error is from **bad signing credentials**, not from `export-env.sh`. Fix one of these:

1. **Use a current IAM key pair** — In IAM, create a new access key, copy both values once, put them in `.env` (or only in `~/.aws/credentials` via `aws configure`).
2. **Bash and `.env`** — If `AWS_SECRET_ACCESS_KEY` (or the access key) contains characters like `$`, `` ` ``, or `!`, unquoted `source` can corrupt the value. Use **single quotes** around the value, e.g. `AWS_SECRET_ACCESS_KEY='wJalr...'`.
3. **Stop duplicating keys** — Delete `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from `.env` and rely on a profile that already works: run `aws sts get-caller-identity` successfully, then run `./export-env.sh` again (same shell picks up `~/.aws`).

## Ansible

The dynamic inventory [`ansible/inventory.sh`](../ansible/inventory.sh) sources **`configure-env/.env`** and uses `JENKINS_EIP` as the target host. Set that IP after Terraform or the AWS console shows the Elastic IP.

## Security

- Do not commit `.env` or real tokens.
- Rotate GitHub PATs and Docker Hub secrets if they are exposed.
- Prefer IAM roles (Jenkins instance profile) over long-lived keys in `.env` where possible.
