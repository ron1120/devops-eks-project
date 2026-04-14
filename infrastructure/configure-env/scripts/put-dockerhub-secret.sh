#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  echo "Copy $ROOT/.env.example to .env and set DOCKERHUB_USERNAME / DOCKERHUB_PASSWORD." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${DOCKERHUB_USERNAME:?Set DOCKERHUB_USERNAME in $ENV_FILE}"
: "${DOCKERHUB_PASSWORD:?Set DOCKERHUB_PASSWORD in $ENV_FILE}"

REGION="${AWS_REGION:-us-east-1}"
SECRET_ID="${SECRET_ID:-DockerHubCredentials}"

SECRET_JSON="$(
  DOCKERHUB_USERNAME="$DOCKERHUB_USERNAME" DOCKERHUB_PASSWORD="$DOCKERHUB_PASSWORD" \
    python3 -c 'import json, os; print(json.dumps({"username": os.environ["DOCKERHUB_USERNAME"], "password": os.environ["DOCKERHUB_PASSWORD"]}))'
)"

aws secretsmanager put-secret-value \
  --secret-id "$SECRET_ID" \
  --region "$REGION" \
  --secret-string "$SECRET_JSON"

echo "Updated secret $SECRET_ID in $REGION."
