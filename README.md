# find-me-flight

Monitors El Al's seat availability API for flights departing from Tel Aviv (TLV). Sends an email alert as soon as a flight with 4 or more available seats is found.

## Setup

**1. Install dependencies**
```bash
pip3 install -r requirements.txt
```

**2. Create a `.env` file** in the project root:
```
SENDER_EMAIL=your@gmail.com
APP_PASSWORD=xxxx xxxx xxxx xxxx
```

To generate a Gmail app password: Google Account → Security → 2-Step Verification → App passwords.

**3. Run**
```bash
caffeinate -i python3 flight_monitor.py
```

`caffeinate -i` prevents the Mac from sleeping for as long as the script runs.

To run in the background and persist after closing the terminal:
```bash
nohup caffeinate -i python3 flight_monitor.py > flight_monitor.log 2>&1 &
tail -f flight_monitor.log   # follow logs
```

## How it works

- Polls the El Al seat availability API every 5 minutes
- Scans `flightsFromIsrael` for any date with `seatCount >= 4`
- Sends an email to the configured recipient listing all matching flights
- Tracks already-notified flight+date pairs to avoid duplicate emails

## Running tests

```bash
python3 -m pytest test_flight_monitor.py -v
```

## Project structure

```
flight_monitor.py        # main script
test_flight_monitor.py   # unit tests
requirements.txt
.env                     # credentials — never committed
```
