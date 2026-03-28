import requests
import json
import smtplib
from email.mime.text import MIMEText
import time
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('APP_PASSWORD')
RECEIVER_EMAIL = 'avivoron@gmail.com'
NTFY_TOPIC = os.getenv('NTFY_TOPIC')  # e.g. "aviv-flights-x7k2"

URL = 'https://www.elal.com/api/SeatAvailability/lang/heb/flights'
HEADERS = {
    'sec-ch-ua-platform': '"macOS"',
    'Referer': 'https://www.elal.com/heb/seat-availability?d=0',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    'sec-ch-ua-mobile': '?0'
}

def fetch_flight_data():
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def find_available_flights(data):
    if not data or 'flightsFromIsrael' not in data:
        return []
    
    found_flights = []
    for destination in data['flightsFromIsrael']:
        dest_code = destination['origin']
        dest_details = destination['flights'][0]['destinationDetails'] if destination['flights'] else {}
        city = dest_details.get('cityName', dest_code)
        country = dest_details.get('countryName', '')
        
        for flight in destination['flights']:
            flight_number = flight['flightNumber']
            for date_info in flight['flightsDates']:
                if 'seatCount' in date_info and date_info['seatCount'] >= 4:
                    found_flights.append({
                        'destination': dest_code,
                        'city': city,
                        'country': country,
                        'flight': flight_number,
                        'date': date_info['flightsDate'],
                        'seats': date_info['seatCount'],
                        'seat_type': date_info.get('seatType', 'N/A')
                    })
    return found_flights

def send_push(flights):
    if not flights or not NTFY_TOPIC:
        return
    lines = [f"{f['flight']} → {f['city']} on {f['date']}: {f['seats']} seats" for f in flights]
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data="\n".join(lines),
            headers={"Title": "El Al seats available!", "Priority": "high", "Tags": "airplane"},
        )
    except Exception as e:
        print(f"Error sending push: {e}")

def send_email(flights):
    if not flights:
        return
    
    # Create message
    message = "Flights from TLV with >=4 seats found:\n\n"
    for flight in flights:
        message += f"- Flight {flight['flight']} to {flight['city']} ({flight['country']}) on {flight['date']}: {flight['seats']} seats\n"
    
    msg = MIMEText(message)
    msg['Subject'] = 'Flight Alert: Seats Available from TLV'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

POLL_INTERVAL_SECONDS = 60  # check every 5 minutes

def main():
    print(f"Starting flight monitor (polling every {POLL_INTERVAL_SECONDS}s)...")
    notified_keys = set()  # avoid duplicate emails for same flight+date

    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking flights...")
        data = fetch_flight_data()
        if data:
            available_flights = find_available_flights(data)
            new_flights = [f for f in available_flights
                           if (f['flight'], f['date']) not in notified_keys]
            if new_flights:
                print(f"Found {len(new_flights)} new flights with >=4 seats — sending email")
                send_email(new_flights)
                send_push(new_flights)
                for f in new_flights:
                    notified_keys.add((f['flight'], f['date']))
            else:
                print(f"No qualifying flights yet ({len(available_flights)} total found)")
        else:
            print("Failed to fetch data")
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()