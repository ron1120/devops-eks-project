#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found. Copy .env.example to .env and fill in values." >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

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
