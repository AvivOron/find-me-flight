import unittest
from unittest.mock import patch, MagicMock
from flight_monitor import find_available_flights, send_email

# Fixture built from the actual API response structure
SAMPLE_RESPONSE = {
    "responseCode": 0,
    "runDateTime": "2026-03-28 14:34",
    "dateRange": {
        "dates": ["28.03", "29.03", "30.03", "31.03", "01.04", "02.04", "03.04", "04.04"]
    },
    "flightsFromIsrael": [
        {
            "origin": "LHR",
            "flights": [
                {
                    "flightCarrier": "LY",
                    "flightNumber": "LY315",
                    "routeFrom": "TLV",
                    "routeTo": "LHR",
                    "segmentDepTime": "06:40",
                    "flightsDates": [
                        {"flightsDate": "28.03"},
                        {"flightsDate": "29.03", "seatCount": 9, "seatType": "Y"},
                        {"flightsDate": "30.03", "seatCount": 0, "seatType": "N/A"},
                        {"flightsDate": "31.03"},
                        {"flightsDate": "01.04"},
                        {"flightsDate": "02.04"},
                        {"flightsDate": "03.04", "seatCount": 9, "seatType": "Y"},
                        {"flightsDate": "04.04"},
                    ],
                    "isFlightAvailable": True,
                    "originDetails": {
                        "destinationName": "נמל התעופה בן גוריון",
                        "cityName": "תל אביב",
                        "countryName": "ישראל"
                    },
                    "destinationDetails": {
                        "destinationName": "הית'רו",
                        "cityName": "London",
                        "countryName": "England",
                        "continentName": "Europe"
                    }
                }
            ]
        },
        {
            "origin": "FCO",
            "flights": [
                {
                    "flightCarrier": "LY",
                    "flightNumber": "LY583",
                    "routeFrom": "TLV",
                    "routeTo": "FCO",
                    "segmentDepTime": "08:00",
                    "flightsDates": [
                        {"flightsDate": "28.03"},
                        {"flightsDate": "29.03", "seatCount": 1, "seatType": "Y"},
                        {"flightsDate": "30.03", "seatCount": 3, "seatType": "Y"},
                        {"flightsDate": "31.03", "seatCount": 4, "seatType": "Y"},
                        {"flightsDate": "01.04"},
                        {"flightsDate": "02.04", "seatCount": 0, "seatType": "N/A"},
                        {"flightsDate": "03.04"},
                        {"flightsDate": "04.04"},
                    ],
                    "isFlightAvailable": True,
                    "originDetails": {
                        "destinationName": "נמל התעופה בן גוריון",
                        "cityName": "תל אביב",
                        "countryName": "ישראל"
                    },
                    "destinationDetails": {
                        "destinationName": "פיומיצ'ינו",
                        "cityName": "Rome",
                        "countryName": "Italy",
                        "continentName": "Europe"
                    }
                }
            ]
        },
        {
            "origin": "VIE",
            "flights": [
                {
                    "flightCarrier": "LY",
                    "flightNumber": "LY363",
                    "routeFrom": "TLV",
                    "routeTo": "VIE",
                    "segmentDepTime": "17:30",
                    "flightsDates": [
                        {"flightsDate": "28.03"},
                        {"flightsDate": "29.03", "seatCount": 0, "seatType": "N/A"},
                        {"flightsDate": "30.03", "seatCount": 0, "seatType": "N/A"},
                        {"flightsDate": "31.03", "seatCount": 0, "seatType": "N/A"},
                        {"flightsDate": "01.04"},
                        {"flightsDate": "02.04"},
                        {"flightsDate": "03.04"},
                        {"flightsDate": "04.04"},
                    ],
                    "isFlightAvailable": False,
                    "originDetails": {
                        "destinationName": "נמל התעופה בן גוריון",
                        "cityName": "תל אביב",
                        "countryName": "ישראל"
                    },
                    "destinationDetails": {
                        "destinationName": "נמל התעופה של וינה",
                        "cityName": "Vienna",
                        "countryName": "Austria",
                        "continentName": "Europe"
                    }
                }
            ]
        }
    ]
}


class TestFindAvailableFlights(unittest.TestCase):

    def test_returns_flights_with_4_or_more_seats(self):
        results = find_available_flights(SAMPLE_RESPONSE)
        for f in results:
            self.assertGreaterEqual(f['seats'], 4)

    def test_excludes_flights_with_fewer_than_4_seats(self):
        results = find_available_flights(SAMPLE_RESPONSE)
        flights = [(f['flight'], f['date']) for f in results]
        # LY583 on 29.03 has 1 seat, 30.03 has 3 seats — both below threshold
        self.assertNotIn(('LY583', '29.03'), flights)
        self.assertNotIn(('LY583', '30.03'), flights)

    def test_excludes_flights_with_zero_seats(self):
        results = find_available_flights(SAMPLE_RESPONSE)
        flights = [(f['flight'], f['date']) for f in results]
        self.assertNotIn(('LY363', '29.03'), flights)
        self.assertNotIn(('LY583', '02.04'), flights)

    def test_excludes_dates_with_no_seatcount_field(self):
        # Dates without a seatCount key at all should not appear
        results = find_available_flights(SAMPLE_RESPONSE)
        flights = [(f['flight'], f['date']) for f in results]
        self.assertNotIn(('LY315', '28.03'), flights)
        self.assertNotIn(('LY315', '31.03'), flights)

    def test_includes_exactly_4_seats(self):
        # LY583 on 31.03 has exactly 4 seats — boundary case
        results = find_available_flights(SAMPLE_RESPONSE)
        flights = [(f['flight'], f['date']) for f in results]
        self.assertIn(('LY583', '31.03'), flights)

    def test_result_fields_are_populated(self):
        results = find_available_flights(SAMPLE_RESPONSE)
        lhr = next(f for f in results if f['flight'] == 'LY315')
        self.assertEqual(lhr['destination'], 'LHR')
        self.assertEqual(lhr['city'], 'London')
        self.assertEqual(lhr['country'], 'England')
        self.assertEqual(lhr['seat_type'], 'Y')

    def test_empty_response_returns_empty_list(self):
        self.assertEqual(find_available_flights({}), [])
        self.assertEqual(find_available_flights(None), [])

    def test_missing_flights_from_israel_key(self):
        self.assertEqual(find_available_flights({"flightsToIsrael": []}), [])

    def test_destination_with_no_flights_list(self):
        data = {"flightsFromIsrael": [{"origin": "LHR", "flights": []}]}
        self.assertEqual(find_available_flights(data), [])

    def test_all_zero_seats_returns_empty(self):
        data = {
            "flightsFromIsrael": [{
                "origin": "VIE",
                "flights": [{
                    "flightNumber": "LY363",
                    "flightsDates": [
                        {"flightsDate": "29.03", "seatCount": 0, "seatType": "N/A"},
                        {"flightsDate": "30.03", "seatCount": 0, "seatType": "N/A"},
                    ],
                    "destinationDetails": {"cityName": "Vienna", "countryName": "Austria"}
                }]
            }]
        }
        self.assertEqual(find_available_flights(data), [])

    def test_multiple_flights_same_destination(self):
        data = {
            "flightsFromIsrael": [{
                "origin": "LHR",
                "flights": [
                    {
                        "flightNumber": "LY315",
                        "flightsDates": [{"flightsDate": "29.03", "seatCount": 9, "seatType": "Y"}],
                        "destinationDetails": {"cityName": "London", "countryName": "England"}
                    },
                    {
                        "flightNumber": "LY317",
                        "flightsDates": [{"flightsDate": "30.03", "seatCount": 5, "seatType": "Y"}],
                        "destinationDetails": {"cityName": "London", "countryName": "England"}
                    }
                ]
            }]
        }
        results = find_available_flights(data)
        self.assertEqual(len(results), 2)
        self.assertEqual({f['flight'] for f in results}, {'LY315', 'LY317'})


class TestSendEmail(unittest.TestCase):

    def test_does_not_send_for_empty_list(self):
        with patch('smtplib.SMTP') as mock_smtp:
            send_email([])
            mock_smtp.assert_not_called()

    def test_sends_for_non_empty_list(self):
        flights = [{'flight': 'LY315', 'city': 'London', 'country': 'England',
                    'date': '29.03', 'seats': 9, 'seat_type': 'Y'}]
        with patch('smtplib.SMTP') as mock_smtp:
            instance = mock_smtp.return_value
            send_email(flights)
            instance.starttls.assert_called_once()
            instance.sendmail.assert_called_once()
            instance.quit.assert_called_once()

    def test_email_body_contains_flight_details(self):
        flights = [{'flight': 'LY315', 'city': 'London', 'country': 'England',
                    'date': '29.03', 'seats': 9, 'seat_type': 'Y'}]
        with patch('smtplib.SMTP') as mock_smtp:
            instance = mock_smtp.return_value
            send_email(flights)
            _, _, raw_msg = instance.sendmail.call_args[0]
            self.assertIn('LY315', raw_msg)
            self.assertIn('London', raw_msg)
            self.assertIn('29.03', raw_msg)
            self.assertIn('9', raw_msg)

    def test_smtp_error_is_handled_gracefully(self):
        flights = [{'flight': 'LY315', 'city': 'London', 'country': 'England',
                    'date': '29.03', 'seats': 9, 'seat_type': 'Y'}]
        with patch('smtplib.SMTP', side_effect=Exception('connection refused')):
            # Should not raise
            send_email(flights)


if __name__ == '__main__':
    unittest.main()
