#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

postgres_ready() {
python3 <<'END'
import os
import sys
import psycopg2

missing = [n for n in ("DB_NAME", "DB_USER", "DB_PASSWORD") if not os.environ.get(n)]
if missing:
    print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
    sys.exit(2)

try:
    conn = psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        connect_timeout=5,
    )
except psycopg2.OperationalError as e:
    print(f"Database not ready: {e}", file=sys.stderr)
    sys.exit(1)

conn.close()
sys.exit(0)
END
}

until postgres_ready; do
  status=$?
  if [ "$status" -eq 2 ]; then
    echo "Configuration error, not retrying." >&2
    exit 1
  fi
  echo "Waiting for PostgreSQL..." >&2
  sleep 2
done

echo "PostgreSQL is available."

exec "$@"