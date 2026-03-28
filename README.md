# Flight Monitor

This script monitors El Al's seat availability API for flights from Tel Aviv (TLV) to various destinations. When it finds flights with 4 or more seats available, it sends an email notification.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure email settings in `flight_monitor.py`:
   - Replace `SENDER_EMAIL` with your Gmail address
   - Replace `SENDER_PASSWORD` with your Gmail app password (not your regular password)
     - To get an app password: Go to Google Account settings > Security > 2-Step Verification > App passwords
   - The receiver email is already set to `avivoron@gmail.com`

3. Run the script:
   ```bash
   python flight_monitor.py
   ```

The script will check for available flights every 5 minutes and send email notifications when flights with >=4 seats are found.

## How it works

- Fetches data from El Al's seat availability API
- Parses flights from Israel (TLV) to other destinations
- Checks for dates with seatCount >= 4
- Sends email with flight details when found
- Avoids duplicate notifications for the same flight/date combination

## Note

Make sure to enable 2-factor authentication on your Gmail account and generate an app password for this script to work.