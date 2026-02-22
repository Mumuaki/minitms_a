#!/usr/bin/env bash
# Test GPS location refresh on VPS. Run from server: bash scripts/vps-test-gps-refresh.sh
# Requires: BACKEND_URL (default http://127.0.0.1:8000), and either:
#   - MINITMS_USER + MINITMS_PASSWORD for login, or
#   - TOKEN=... (Bearer token from browser after login)
# Optional: VEHICLE_PLATE (default BT152DH) to refresh that vehicle.

set -e
cd "$(dirname "$0")/.."
BASE_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
API="${BASE_URL}/api/v1"
PLATE="${VEHICLE_PLATE:-BT152DH}"

echo "=== MiniTMS GPS refresh test ==="
echo "Backend: $BASE_URL"
echo "Vehicle plate: $PLATE"
echo ""

# Get token
if [ -n "$TOKEN" ]; then
  echo "Using provided TOKEN."
  AUTH_HEADER="Authorization: Bearer $TOKEN"
else
  if [ -z "$MINITMS_USER" ] || [ -z "$MINITMS_PASSWORD" ]; then
    echo "Set MINITMS_USER and MINITMS_PASSWORD, or TOKEN (Bearer from browser)."
    echo "Example: MINITMS_USER=admin MINITMS_PASSWORD=yourpass bash scripts/vps-test-gps-refresh.sh"
    exit 1
  fi
  echo "Logging in..."
  LOGIN=$(curl -sf -X POST "$API/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$MINITMS_USER&password=$MINITMS_PASSWORD")
  TOKEN=$(echo "$LOGIN" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
  if [ -z "$TOKEN" ]; then
    echo "Login failed. Response: $LOGIN"
    exit 1
  fi
  AUTH_HEADER="Authorization: Bearer $TOKEN"
  echo "Login OK."
fi

# List fleet and find vehicle
echo ""
echo "Fetching fleet..."
FLEET=$(curl -sf -H "$AUTH_HEADER" "$API/fleet/")
VID=$(echo "$FLEET" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for v in data:
    lp = (v.get('license_plate') or '').replace(' ','').upper()
    if lp == '$PLATE'.replace(' ','').upper():
        print(v['id'])
        print('Location:', v.get('current_location') or '(none)')
        print('GPS tracker_id:', v.get('gps_tracker_id') or '(none)')
        break
else:
    sys.exit(1)
" 2>/dev/null || true)

if [ -z "$VID" ]; then
  # Try without python: simple grep (id might be first number after "license_plate":"BT152DH" or similar)
  echo "Could not parse fleet (python3 required). Raw fleet (first 500 chars):"
  echo "$FLEET" | head -c 500
  echo ""
  echo "Get vehicle id from above and run: curl -X POST -H \"$AUTH_HEADER\" $API/fleet/ID/refresh-location"
  exit 1
fi

# VID may be multiple lines (id, then location, then gps_tracker_id from the python print)
VEHICLE_ID=$(echo "$VID" | head -1)
echo "Vehicle ID: $VEHICLE_ID"
echo "Current location (before refresh): $(echo "$VID" | sed -n '2s/Location: //p')"
echo "GPS tracker_id: $(echo "$VID" | sed -n '3s/GPS tracker_id: //p')"
echo ""

# Refresh location
echo "Calling POST $API/fleet/$VEHICLE_ID/refresh-location ..."
REFRESH=$(curl -sf -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" "$API/fleet/$VEHICLE_ID/refresh-location")
NEW_LOC=$(echo "$REFRESH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('current_location') or '(none)')" 2>/dev/null || echo "(parse error)")
echo "Location after refresh: $NEW_LOC"
echo ""

# Show Dozor status and first vehicle keys (for debugging API shape)
echo "--- GPS Dozor status ---"
curl -sf -H "$AUTH_HEADER" "$API/gps/status" | python3 -m json.tool 2>/dev/null || curl -sf -H "$AUTH_HEADER" "$API/gps/status"
echo ""
echo "--- First vehicle from Dozor (keys) ---"
curl -sf -H "$AUTH_HEADER" "$API/gps/vehicles" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        print('Keys:', list(data[0].keys()))
        print('Sample:', json.dumps(data[0], indent=2, default=str)[:800])
    else:
        print('(empty list)')
except Exception as e:
    print('Error:', e)
" 2>/dev/null || true

echo ""
echo "=== Done. Check backend logs: docker compose logs --tail=50 backend | grep -i dozor ==="
