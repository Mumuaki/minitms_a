#!/bin/bash
# minitms-backup-gate.sh - decides whether a date qualifies for a MiniTMS DB backup.
#
# A dump is allowed only when BOTH hold for the backup date:
#   (a) the application was CALLED that date (a real request, not a health/docs probe)
#   (b) for the 20 minutes following the FIRST call that date it ran CLEAN:
#         - no Traceback / ERROR / CRITICAL in the app containers
#         - no restart of the app containers
#
# Usage: minitms-backup-gate.sh [YYYY-MM-DD]   (default: yesterday, UTC)
#        minitms-backup-gate.sh --force        (allow unconditionally; manual use)
# Exit 0 = back up, exit 1 = skip. Every decision states its reason on stdout, so
# the nightly log can never show a missing backup without an explanation.
set -uo pipefail

WINDOW_MIN=20
# The API is the entry point. Health probes fire every 15s and docs endpoints are
# static, so neither counts as the application being called.
CALL_CONTAINER=minitms-core-api
# Containers whose health we judge. scraping-worker is deliberately excluded: it
# drives a real browser against Trans.eu, so remote-site failures are not app bugs.
HEALTH_CONTAINERS="minitms-core-api minitms-celery-worker minitms-celery-beat"
# If the logs no longer cover the date, nothing can be verified. 1 = back up anyway
# (fail safe towards having a backup), 0 = skip.
FAILSAFE_ON_UNVERIFIABLE=1

if [ "${1:-}" = "--force" ]; then echo "FORCED: backup gate bypassed"; exit 0; fi

DAY="${1:-$(date -u -d 'yesterday' +%F)}"
day_start="${DAY}T00:00:00"
day_end="${DAY}T23:59:59"
start_ep=$(date -u -d "$day_start" +%s)
end_ep=$(date -u -d "$day_end" +%s)

# ---- does the retained log even cover that day? (container recreate resets logs) ----
earliest_full=$(docker logs -t "$CALL_CONTAINER" 2>/dev/null | head -1 | awk '{print $1}')
if [ -n "$earliest_full" ]; then
  earliest_sec="${earliest_full%%.*}"
  e_ep=$(date -u -d "$earliest_sec" +%s 2>/dev/null || echo 0)
  if [ "$e_ep" -gt "$end_ep" ]; then
    if [ "$FAILSAFE_ON_UNVERIFIABLE" = "1" ]; then
      echo "WARN: logs only start at $earliest_sec, after $DAY - cannot verify; backing up anyway (FAILSAFE_ON_UNVERIFIABLE=1)"
      exit 0
    fi
    echo "SKIP: logs only start at $earliest_sec and do not cover $DAY - cannot verify"
    exit 1
  fi
fi

# ---- (a) was the application called that date? ----
calls=$(docker logs -t --since "$day_start" --until "$day_end" "$CALL_CONTAINER" 2>&1 \
        | grep -E '"(GET|POST|PUT|PATCH|DELETE) /' \
        | grep -vE '"(GET|POST) /(health|docs|openapi.json)' || true)
n=$(printf '%s' "$calls" | grep -c . || true)
if [ "$n" -eq 0 ]; then
  echo "SKIP: condition (a) failed - application was not called on $DAY"
  exit 1
fi

first_ts=$(printf '%s\n' "$calls" | head -1 | awk '{print $1}')
first_sec="${first_ts%%.*}"
f_ep=$(date -u -d "$first_sec" +%s)
w_ep=$((f_ep + WINDOW_MIN * 60))
window_end=$(date -u -d "@$w_ep" +%Y-%m-%dT%H:%M:%S)
echo "INFO: $n call(s) on $DAY; first at $first_sec; clean window $first_sec .. $window_end"

# ---- (b) clean for WINDOW_MIN after that first call? ----
errs=0; starts=0
for c in $HEALTH_CONTAINERS; do
  win=$(docker logs -t --since "$first_sec" --until "$window_end" "$c" 2>&1 || true)
  e=$(printf '%s' "$win" | grep -cE 'Traceback|CRITICAL:|ERROR:' || true)
  s=$(printf '%s' "$win" | grep -cE 'Application startup complete|Uvicorn running on|celery@.*ready|beat: Starting' || true)
  errs=$((errs + e)); starts=$((starts + s))
  if [ "$e" -ne 0 ]; then
    echo "       errors in $c:"
    printf '%s\n' "$win" | grep -E 'Traceback|CRITICAL:|ERROR:' | head -3 | sed 's/^/         /'
  fi
done

[ "$errs" -eq 0 ] || { echo "SKIP: condition (b) failed - $errs error line(s) within $WINDOW_MIN min of the first call"; exit 1; }
[ "$starts" -eq 0 ] || { echo "SKIP: condition (b) failed - the application (re)started within $WINDOW_MIN min of the first call"; exit 1; }

for c in $HEALTH_CONTAINERS; do
  started=$(docker inspect "$c" --format '{{.State.StartedAt}}' 2>/dev/null || true)
  [ -n "$started" ] || continue
  s_sec="${started%%.*}"; s_ep=$(date -u -d "$s_sec" +%s 2>/dev/null || echo 0)
  if [ "$s_ep" -gt "$f_ep" ] && [ "$s_ep" -lt "$w_ep" ]; then
    echo "SKIP: condition (b) failed - $c restarted at $s_sec inside the clean window"
    exit 1
  fi
done

echo "PASS: $DAY - called $n time(s) and ran clean for $WINDOW_MIN min afterwards"
exit 0
