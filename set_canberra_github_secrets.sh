#!/usr/bin/env bash

set -euo pipefail

environment="${1:-mybus}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: authenticate first with: gh auth login" >&2
  exit 1
fi

read -r -p "Canberra Client ID: " client_id
read -r -s -p "Canberra Client Secret: " client_secret
echo

if [[ -z "$client_id" || -z "$client_secret" ]]; then
  echo "Error: both values are required." >&2
  exit 1
fi

printf '%s' "$client_id" | gh secret set CANBERRA_GTFS_CLIENT_ID --env "$environment"
printf '%s' "$client_secret" | gh secret set CANBERRA_GTFS_CLIENT_SECRET --env "$environment"

unset client_id client_secret
echo "Canberra secrets configured in GitHub environment: $environment"
