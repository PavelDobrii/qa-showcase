#!/usr/bin/env bash
# Start the local copy of the Toolshop app and fill its database with demo data.
# After this script: UI on http://localhost:4200, API on http://localhost:8091.
set -euo pipefail

cd "$(dirname "$0")"
compose=(docker compose -f toolshop-compose.yml)

# Try a check every 5 seconds, for up to 5 minutes.
wait_for() {
  local what=$1
  shift
  for _ in $(seq 1 60); do
    if "$@" > /dev/null 2>&1; then
      echo "$what is ready"
      return 0
    fi
    sleep 5
  done
  echo "$what is not ready after 5 minutes" >&2
  "${compose[@]}" logs --tail 50 >&2
  return 1
}

"${compose[@]}" up --detach --quiet-pull

wait_for "Database" "${compose[@]}" exec -T mariadb mysqladmin ping -h localhost -u root -proot
"${compose[@]}" exec -T laravel-api php artisan migrate:refresh --seed --force
wait_for "API" curl --fail --silent http://localhost:8091/products
wait_for "UI" curl --fail --silent http://localhost:4200
