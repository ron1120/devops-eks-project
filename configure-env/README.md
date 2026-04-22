# configure-env

Local environment file for this repo: **Jenkins host IP** (for Ansible) and **Docker Hub / GitHub / Slack** values synced to **AWS Secrets Manager**.

`.env` is gitignored.

```bash
cp .env.example .env
```

---

## Variables

| Variable                                      | Purpose                                                                                  |
| --------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `AWS_REGION`                                  | AWS region (e.g. `us-east-1`) used by the CLI and Secrets Manager.                       |
| `JENKINS_EIP`                                 | Jenkins EC2 Elastic IP, consumed by [`../ansible/inventory.sh`](../ansible/inventory.sh). |
| `DOCKERHUB_USERNAME` / `DOCKERHUB_PASSWORD`   | Docker Hub credentials pushed to Secrets Manager.                                        |
| `AWS_DOCKERHUB_SECRET_ID`                     | Secrets Manager secret name (e.g. `DockerHubCredentials`).                               |
| `GIT_USERNAME` / `GIT_API_TOKEN`              | GitHub user + fine-grained PAT for **Tag Release** in `jenkins/Jenkinsfile.cli`.          |
| `AWS_GIT_SECRET_ID`                           | Secrets Manager secret name for GitHub (e.g. `RonGitUser`).                              |
| `SLACK_WEBHOOK_URL`                           | Slack Incoming Webhook used by pipeline failure notifications.                            |
| `AWS_SLACK_SECRET_ID`                         | Secrets Manager secret name for Slack.                                                   |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Optional. Otherwise the CLI uses your usual provider chain (profile, SSO, instance role). |

---

## Sync to AWS Secrets Manager

```bash
cd configure-env
./export-env.sh
```

The script loads `.env` and calls `aws secretsmanager put-secret-value` for each secret. Your AWS identity must be allowed to update them.

---

## Troubleshooting

**`InvalidSignatureException` / "signature we calculated does not match"** — bad signing credentials, not the script.

1. Create a new IAM access key and put it in `.env` (or via `aws configure`).
2. Quote values with special chars: `AWS_SECRET_ACCESS_KEY='wJalr...'` — unquoted `source` corrupts `$`, `` ` ``, `!`.
3. Or remove the keys from `.env` and rely on a profile that already works (`aws sts get-caller-identity`).

---

## Security

- Never commit `.env` or real tokens.
- Rotate GitHub PATs and Docker Hub secrets if exposed.
- Prefer IAM roles (Jenkins instance profile) over long-lived keys.
