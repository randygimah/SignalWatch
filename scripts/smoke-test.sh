#!/bin/sh
set -eu

API_URL="${SIGNALWATCH_API_URL:-http://localhost:8000}"
WEB_URL="${SIGNALWATCH_WEB_URL:-http://localhost:5173}"

health="$(curl --fail --silent --show-error "${API_URL}/api/v1/health")"
overview="$(curl --fail --silent --show-error "${API_URL}/api/v1/overview?sensor_id=RX-NORTH")"
web_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "${WEB_URL}")"

echo "$health" | grep --quiet '"status":"ok"'
echo "$overview" | grep --quiet '"incidents"'
test "$web_status" = "200"

echo "SignalWatch smoke test passed: API health, analytics overview, and dashboard are available."
