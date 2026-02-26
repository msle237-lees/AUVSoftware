#!/usr/bin/env bash
# smoke_api.sh
# Smoke-test script for the AUVSoftware FastAPI API layer (routes-based).
#
# Routes pulled from your Swagger PDF:
# - runs:   GET /runs, POST /runs, GET /runs/latest, GET /runs/{run_id}
# - inputs: POST /inputs, GET /inputs/latest, GET /inputs/by-run/{run_id}
# - imu:    POST /imu,    GET /imu/latest,    GET /imu/by-run/{run_id}
# - depth:  POST /depth,  GET /depth/latest,  GET /depth/by-run/{run_id}
# - power:  POST /power,  GET /power/latest,  GET /power/by-run/{run_id}
# - motor:  POST /motor,  GET /motor/latest,  GET /motor/by-run/{run_id}
# - servo:  POST /servo,  GET /servo/latest,  GET /servo/by-run/{run_id}
#
# Requirements: bash, curl
# Optional: jq (recommended). If jq isn't installed, Python is used for basic JSON parsing.
#
# Usage:
#   ./smoke_api.sh
#   API_BASE_URL="http://localhost:8000" ./smoke_api.sh
#   ./smoke_api.sh --base-url http://127.0.0.1:8000 --verbose
#
# Exit codes:
#   0 success
#   1 failure

set -Eeuo pipefail

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
VERBOSE=0
TIMEOUT_S="${SMOKE_TIMEOUT_S:-10}"
API_PREFIX="${API_PREFIX:-}"  # set to "/api" or "/api/v1" if you mount under a prefix

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) BASE_URL="${2:?missing --base-url value}"; shift 2 ;;
    --timeout)  TIMEOUT_S="${2:?missing --timeout value}"; shift 2 ;;
    --verbose|-v) VERBOSE=1; shift ;;
    --help|-h) sed -n '1,120p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

log()  { echo "[$(date +'%H:%M:%S')] $*"; }
vlog() { [[ "$VERBOSE" -eq 1 ]] && log "$@"; }
die()  { echo "ERROR: $*" >&2; exit 1; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"; }

base() { echo "${BASE_URL%/}${API_PREFIX}$1"; }

json_get() {
  local json="$1"
  local expr="$2"

  if command -v jq >/dev/null 2>&1; then
    echo "$json" | jq -er "$expr"
  else
    python3 - <<PY
import json,sys
data=json.loads(sys.stdin.read())
expr=${expr!r}
if not expr.startswith(".") or any(c in expr for c in " []()"):
    raise SystemExit("Unsupported expr without jq: "+expr)
key=expr[1:]
val=data.get(key, None)
if val is None:
    raise SystemExit(1)
print(val)
PY
  fi
}

http() {
  # http METHOD URL [JSON_BODY]
  local method="$1"
  local url="$2"
  local body="${3:-}"

  local args=(
    -sS
    --connect-timeout "$TIMEOUT_S"
    --max-time "$TIMEOUT_S"
    -H "Accept: application/json"
    -w $'\n%{http_code}'
  )

  if [[ "$VERBOSE" -eq 1 ]]; then args+=(-v); fi

  if [[ -n "$body" ]]; then
    args+=(-H "Content-Type: application/json" -d "$body")
  fi

  local resp
  resp="$(curl "${args[@]}" -X "$method" "$url")"

  local status="${resp##*$'\n'}"
  local content="${resp%$'\n'*}"
  printf '%s\n%s\n' "$status" "$content"
}

expect_2xx() {
  local name="$1" status="$2" body="$3"
  if [[ ! "$status" =~ ^2[0-9]{2}$ ]]; then
    echo "----- $name failed -----" >&2
    echo "URL/Step: $name" >&2
    echo "Status: $status" >&2
    echo "Body: $body" >&2
    die "$name returned non-2xx"
  fi
}

expect_field() {
  local name="$1" json="$2" expr="$3"
  local val
  if ! val="$(json_get "$json" "$expr" 2>/dev/null)"; then
    echo "----- $name missing field $expr -----" >&2
    echo "$json" >&2
    die "$name response missing $expr"
  fi
  vlog "$name: $expr = $val"
}

ts_us() {
  python3 - <<'PY'
import time
print(int(time.time() * 1_000_000))
PY
}

# ---- Routes (from your Swagger PDF) -----------------------------------------
OPENAPI="/openapi.json"

RUNS="/runs"
RUNS_LATEST="/runs/latest"

INPUTS="/inputs"
INPUTS_LATEST="/inputs/latest"
INPUTS_BY_RUN="/inputs/by-run"        # /{run_id}

IMU="/imu"
IMU_LATEST="/imu/latest"
IMU_BY_RUN="/imu/by-run"              # /{run_id}

DEPTH="/depth"
DEPTH_LATEST="/depth/latest"
DEPTH_BY_RUN="/depth/by-run"          # /{run_id}

POWER="/power"
POWER_LATEST="/power/latest"
POWER_BY_RUN="/power/by-run"          # /{run_id}

MOTOR="/motor"
MOTOR_LATEST="/motor/latest"
MOTOR_BY_RUN="/motor/by-run"          # /{run_id}

SERVO="/servo"
SERVO_LATEST="/servo/latest"
SERVO_BY_RUN="/servo/by-run"          # /{run_id}

# ---- Start ------------------------------------------------------------------
need_cmd curl
log "Base URL: $BASE_URL (API_PREFIX='${API_PREFIX}')"
command -v jq >/dev/null 2>&1 && vlog "jq detected" || vlog "jq not found (python fallback parsing)"

# OpenAPI preflight
log "Preflight: GET $(base "$OPENAPI")"
readarray -t pre < <(http "GET" "$(base "$OPENAPI")")
expect_2xx "OpenAPI preflight" "${pre[0]}" "$(printf '%s\n' "${pre[@]:1}")"
log "OpenAPI reachable"

# ---- Create Run -------------------------------------------------------------
run_payload="$(cat <<JSON
{
  "name": "smoke-test-$(date +%Y%m%d-%H%M%S)",
  "platform": "smoke",
  "vehicle": "test-vehicle",
  "operator": "smoke-script",
  "notes": "routes-based smoke test",
  "config_json": "{\"smoke\": true}"
}
JSON
)"

log "Create Run: POST $(base "$RUNS")"
readarray -t rr < <(http "POST" "$(base "$RUNS")" "$run_payload")
run_status="${rr[0]}"
run_body="$(printf '%s\n' "${rr[@]:1}")"
expect_2xx "Create Run" "$run_status" "$run_body"
expect_field "Create Run" "$run_body" ".id"
RUN_ID="$(json_get "$run_body" ".id")"
log "Run created: run_id=$RUN_ID"

# Verify run fetch + latest
log "Get Run: GET $(base "$RUNS/$RUN_ID")"
readarray -t gr < <(http "GET" "$(base "$RUNS/$RUN_ID")")
expect_2xx "Get Run" "${gr[0]}" "$(printf '%s\n' "${gr[@]:1}")"

log "Get Latest Run: GET $(base "$RUNS_LATEST")"
readarray -t glr < <(http "GET" "$(base "$RUNS_LATEST")")
expect_2xx "Get Latest Run" "${glr[0]}" "$(printf '%s\n' "${glr[@]:1}")"

T0="$(ts_us)"

# ---- POST helpers -----------------------------------------------------------
post_and_check_latest_and_by_run() {
  # Args:
  #   name, post_path, latest_path, by_run_path, payload_json
  local name="$1"
  local post_path="$2"
  local latest_path="$3"
  local by_run_path="$4"
  local payload="$5"

  log "Create $name: POST $(base "$post_path")"
  readarray -t pr < <(http "POST" "$(base "$post_path")" "$payload")
  local st="${pr[0]}"
  local bd="$(printf '%s\n' "${pr[@]:1}")"
  expect_2xx "Create $name" "$st" "$bd"
  expect_field "Create $name" "$bd" ".id"
  expect_field "Create $name" "$bd" ".run_id"

  local created_id
  created_id="$(json_get "$bd" ".id")"
  log "$name created: id=$created_id"

  # Latest for this run_id
  log "Get Latest $name (run-scoped): GET $(base "$latest_path")?run_id=$RUN_ID"
  readarray -t lr < <(http "GET" "$(base "$latest_path")?run_id=$RUN_ID")
  expect_2xx "Get Latest $name" "${lr[0]}" "$(printf '%s\n' "${lr[@]:1}")"

  # By-run list
  log "List $name For Run: GET $(base "$by_run_path/$RUN_ID")?limit=10"
  readarray -t br < <(http "GET" "$(base "$by_run_path/$RUN_ID")?limit=10")
  expect_2xx "List $name For Run" "${br[0]}" "$(printf '%s\n' "${br[@]:1}")"

  # Basic sanity: ensure array contains at least one element with matching run_id (uses jq if present)
  if command -v jq >/dev/null 2>&1; then
    local ok
    ok="$(printf '%s\n' "${br[@]:1}" | jq -er --argjson rid "$RUN_ID" 'map(select(.run_id == $rid)) | length')"
    [[ "$ok" -ge 1 ]] || die "List $name For Run returned 0 items for run_id=$RUN_ID"
    vlog "List $name For Run contains $ok items for run_id=$RUN_ID"
  fi
}

# ---- Inputs (Control Input) -------------------------------------------------
inputs_payload="$(cat <<JSON
{
  "run_id": $RUN_ID,
  "t_us": $((T0 + 1000)),
  "seq": 1,
  "x": 0.1,
  "y": -0.2,
  "z": 0.3,
  "yaw": 0.05,
  "s1": 10,
  "s2": 20,
  "s3": 30
}
JSON
)"
post_and_check_latest_and_by_run "Control Input" "$INPUTS" "$INPUTS_LATEST" "$INPUTS_BY_RUN" "$inputs_payload"

# ---- IMU --------------------------------------------------------------------
imu_payload="$(cat <<JSON
{
  "run_id": $RUN_ID,
  "t_us": $((T0 + 2000)),
  "seq": 2,
  "ax": 0.01,
  "ay": 0.02,
  "az": 9.81,
  "gx": 0.001,
  "gy": 0.002,
  "gz": 0.003,
  "mx": 0.1,
  "my": 0.2,
  "mz": 0.3,
  "temp_c": 21.0
}
JSON
)"
post_and_check_latest_and_by_run "IMU Sample" "$IMU" "$IMU_LATEST" "$IMU_BY_RUN" "$imu_payload"

# ---- Depth ------------------------------------------------------------------
depth_payload="$(cat <<JSON
{
  "run_id": $RUN_ID,
  "t_us": $((T0 + 3000)),
  "seq": 3,
  "depth_m": 1.234,
  "pressure_pa": 101325.0,
  "temp_c": 20.5
}
JSON
)"
post_and_check_latest_and_by_run "Depth Sample" "$DEPTH" "$DEPTH_LATEST" "$DEPTH_BY_RUN" "$depth_payload"

# ---- Power ------------------------------------------------------------------
power_payload="$(cat <<JSON
{
  "run_id": $RUN_ID,
  "t_us": $((T0 + 4000)),
  "seq": 4,
  "bat1_voltage_v": 12.1,
  "bat1_current_a": 1.2,
  "bat1_temp_c": 25.0,
  "bat2_voltage_v": 12.0,
  "bat2_current_a": 1.1,
  "bat2_temp_c": 25.2,
  "bat3_voltage_v": 11.9,
  "bat3_current_a": 1.0,
  "bat3_temp_c": 24.8
}
JSON
)"
post_and_check_latest_and_by_run "Power Sample" "$POWER" "$POWER_LATEST" "$POWER_BY_RUN" "$power_payload"

# ---- Motor ------------------------------------------------------------------
motor_payload="$(cat <<JSON
{
  "run_id": $RUN_ID,
  "t_us": $((T0 + 5000)),
  "seq": 5,
  "m1": 128,
  "m2": 128,
  "m3": 128,
  "m4": 128,
  "m5": 128,
  "m6": 128,
  "m7": 128,
  "m8": 128
}
JSON
)"
post_and_check_latest_and_by_run "Motor Output" "$MOTOR" "$MOTOR_LATEST" "$MOTOR_BY_RUN" "$motor_payload"

# ---- Servo ------------------------------------------------------------------
servo_payload="$(cat <<JSON
{
  "run_id": $RUN_ID,
  "t_us": $((T0 + 6000)),
  "seq": 6,
  "s1": 64,
  "s2": 128,
  "s3": 192
}
JSON
)"
post_and_check_latest_and_by_run "Servo Output" "$SERVO" "$SERVO_LATEST" "$SERVO_BY_RUN" "$servo_payload"

log "Smoke test PASSED ✅"