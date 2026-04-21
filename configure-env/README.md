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
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Optional. Documented for local use; Jenkins CD normally uses the EC2 instance profile instead. |

## Sync secrets to AWS

Run from this directory (requires AWS CLI with permission to update the secrets):

```bash
./export-env.sh
```

This reads `.env` and runs `aws secretsmanager put-secret-value` for:

- `AWS_DOCKERHUB_SECRET_ID` — JSON `username` / `password` from Docker Hub vars.
- `AWS_GIT_SECRET_ID` — JSON `username` / `password` from Git GitHub vars (`GIT_API_TOKEN` is the password field).

## Ansible

The dynamic inventory [`ansible/inventory.sh`](../ansible/inventory.sh) sources **`configure-env/.env`** and uses `JENKINS_EIP` as the target host. Set that IP after Terraform or the AWS console shows the Elastic IP.

## Security

- Do not commit `.env` or real tokens.
- Rotate GitHub PATs and Docker Hub secrets if they are exposed.
- Prefer IAM roles (Jenkins instance profile) over long-lived keys in `.env` where possible.
