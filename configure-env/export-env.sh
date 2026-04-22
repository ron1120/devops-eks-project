#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found. Copy .env.example to .env and fill in values." >&2
  exit 1
fi

set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

export AWS_PAGER=

# Docker Hub
aws secretsmanager put-secret-value \
  --secret-id "$AWS_DOCKERHUB_SECRET_ID" \
  --region "$AWS_REGION" \
  --secret-string "{\"username\":\"${DOCKERHUB_USERNAME}\",\"password\":\"${DOCKERHUB_PASSWORD}\"}"

echo "Updated secret: $AWS_DOCKERHUB_SECRET_ID"

# GitHub (for Tag Release)
aws secretsmanager put-secret-value \
  --secret-id "$AWS_GIT_SECRET_ID" \
  --region "$AWS_REGION" \
  --secret-string "{\"username\":\"${GIT_USERNAME}\",\"password\":\"${GIT_API_TOKEN}\"}"

echo "Updated secret: $AWS_GIT_SECRET_ID"

# Slack Incoming Webhook (used by Jenkinsfile.* post.failure notifications).
# Create the secret on first run, otherwise update the existing value.
if aws secretsmanager describe-secret \
     --secret-id "$AWS_SLACK_SECRET_ID" \
     --region "$AWS_REGION" >/dev/null 2>&1; then
  aws secretsmanager put-secret-value \
    --secret-id "$AWS_SLACK_SECRET_ID" \
    --region "$AWS_REGION" \
    --secret-string "$SLACK_WEBHOOK_URL"
else
  aws secretsmanager create-secret \
    --name "$AWS_SLACK_SECRET_ID" \
    --region "$AWS_REGION" \
    --secret-string "$SLACK_WEBHOOK_URL" >/dev/null
fi

echo "Updated secret: $AWS_SLACK_SECRET_ID"
