# CLAUDE.md

## Project overview

Python script that polls the El Al seat availability API every ~2 minutes and sends an email + iPhone push notification (via ntfy.sh) when a TLV-departing flight has 4+ available seats.

## Commands

```bash
# Run (caffeinate prevents Mac from sleeping)
caffeinate -i python3 flight_monitor.py

# Run in background (macOS)
nohup caffeinate -i python3 -u flight_monitor.py > flight_monitor.log 2>&1 &

# Run in background (Linux/Pi)
nohup python3 -u flight_monitor.py > flight_monitor.log 2>&1 &

# Tests
python3 -m pytest test_flight_monitor.py -v

# Install deps
pip3 install -r requirements.txt
```

## Key files

- `flight_monitor.py` — main script: fetching, filtering, emailing, polling loop
- `test_flight_monitor.py` — unit tests using the real API response structure as fixtures
- `.env` — credentials (never commit this)

## Environment variables (`.env`)

| Variable | Description |
|---|---|
| `SENDER_EMAIL` | Gmail address used to send alerts |
| `APP_PASSWORD` | Gmail app password (not the account password) |
| `NTFY_TOPIC` | ntfy.sh topic name for iPhone push notifications (optional) |

## API

Endpoint: `GET https://www.elal.com/api/SeatAvailability/lang/heb/flights`

Response has two top-level arrays:
- `flightsFromIsrael` — TLV departures (what we monitor). The `origin` field is the **destination** airport code.
- `flightsToIsrael` — inbound flights (ignored)

A date entry only has `seatCount` when there is some seat data; missing `seatCount` means no data for that date (not zero).

## Behaviour notes

- Polls every 120 seconds base (`POLL_INTERVAL_SECONDS`) with ±30s random jitter to avoid bot detection
- Uses a persistent `requests.Session()` so cookies are reused across requests (reduces challenge-page responses)
- Deduplicates by `(flightNumber, date)` — each combo is notified at most once per process run
- SMTP and ntfy errors are caught and logged; the polling loop continues
- Push notifications sent via `POST https://ntfy.sh/{NTFY_TOPIC}` — skipped silently if `NTFY_TOPIC` is unset
