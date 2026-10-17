#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
python -m scripts.init_db
exec uvicorn main:app --host 0.0.0.0 --port 8090 --reload