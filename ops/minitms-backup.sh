#!/bin/bash
# MiniTMS nightly database backup.
#
# A dump is created ONLY for a date that passes the backup gate:
#   (a) the application was CALLED that date, and
#   (b) it ran CLEAN (no errors, no restarts) for 20 min after the first call.
# See /usr/local/bin/minitms-backup-gate.sh for the exact rules.
#
# Overrides:
#   MINITMS_BACKUP_FORCE=1   bypass the gate (manual/disaster-recovery use)
#   MINITMS_BACKUP_DATE=Y-M-D  evaluate a specific date (testing)
set -uo pipefail

BACKUP_DIR=/var/backups/minitms
KEEP_DAYS=14
ENV_FILE=/opt/minitms/backend/.env
CONTAINER=minitms-postgres
LOG=/var/log/minitms-backup.log
GATE=/usr/local/bin/minitms-backup-gate.sh

log() { echo "$(date -Is) $*" >> "$LOG"; }

mkdir -p "$BACKUP_DIR"

# ---- backup gate: only back up dates the app was called and stayed clean ----
if [ "${MINITMS_BACKUP_FORCE:-0}" = "1" ]; then
  log "GATE: bypassed via MINITMS_BACKUP_FORCE=1 - creating the dump regardless"
else
  gate_args=""
  [ -n "${MINITMS_BACKUP_DATE:-}" ] && gate_args="$MINITMS_BACKUP_DATE"
  if "$GATE" $gate_args >> "$LOG" 2>&1; then
    log "GATE: passed"
  else
    log "SKIPPED: gate refused this date (reason logged above) - no dump created"
    exit 0
  fi
fi

URL=$(grep -m1 -E "^[[:space:]]*DATABASE_URL=" "$ENV_FILE" | cut -d= -f2- | tr -d "\r")
if [ -z "$URL" ]; then log "ERROR: DATABASE_URL not found in $ENV_FILE"; exit 1; fi

TS=$(date +%Y%m%d-%H%M%S)
OUT="$BACKUP_DIR/minitms-$TS.sql.gz"

if ! docker exec "$CONTAINER" pg_dump "$URL" --clean --if-exists 2>>"$LOG" | gzip -9 > "$OUT"; then
  log "ERROR: pg_dump failed"; rm -f "$OUT"; exit 1
fi

if [ ! -s "$OUT" ] || ! gzip -t "$OUT" 2>/dev/null; then
  log "ERROR: backup missing or corrupt: $OUT"; rm -f "$OUT"; exit 1
fi

if ! gunzip -c "$OUT" | grep -q "public.users"; then
  log "ERROR: dump lacks public.users - treating as failed"; rm -f "$OUT"; exit 1
fi

PRUNED=$(find "$BACKUP_DIR" -maxdepth 1 -name "minitms-*.sql.gz" -type f -mtime +"$KEEP_DAYS" -print -delete | wc -l)
log "OK $OUT ($(du -h "$OUT" | cut -f1)) pruned=$PRUNED"
exit 0
