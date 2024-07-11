import requests
import re
import json
import datetime
import time
from fake_useragent import UserAgent
from threading import Lock
from requests.exceptions import SSLError
from config import REQUEST_TIMEOUT
import logging

tokens = 2
last_request_time = time.time()
lock = Lock()

def get_fake_user_agent_response(url):
    global tokens, last_request_time, lock
    try:
        with lock:
            current_time = time.time()
            time_passed = current_time - last_request_time
            tokens += time_passed
            if tokens > 2:
                tokens = 2

            if tokens >= 1:
                tokens -= 1
            else:
                time_to_wait = 1 - tokens
                time.sleep(time_to_wait)
                tokens = 0

            last_request_time = time.time()

            user_agent = UserAgent()
            random_user_agent = user_agent.random
            headers = {"User-Agent": random_user_agent}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=True)
            return response, None
    
    except requests.exceptions.Timeout:
        return None, "The request timed out. Please try again later."
    except SSLError as e:
        return None, f"SSL error occurred: {e}"
    except requests.exceptions.RequestException as e:
        return None, f"An error occurred: {e}"

def get_data(url):
    response, error = get_fake_user_agent_response(url)
    if error:
        return None, error
    if response is None or response.status_code != 200:
        return None, f"Failed to retrieve data from the server. Status code: {response.status_code if response else 'No response'}"
    return response.text, None

def extract_data(html_data, pnr_number):
    try:
        train_info_pattern = r'"TrainNo":"(.*?)","TrainName":"(.*?)"'
        train_info_match = re.search(train_info_pattern, html_data)

        train_number = train_info_match.group(1) if train_info_match else "N/A"
        train_name = train_info_match.group(2) if train_info_match else "N/A"

        boarding_station_name = re.search(r'"BoardingStationName":"(.*?)"', html_data)
        boarding_station_code = re.search(r'"From":"(.*?)"', html_data)
        destination_station_name = re.search(r'"ReservationUptoName":"(.*?)"', html_data)
        destination_station_code = re.search(r'"To":"(.*?)"', html_data)
        boarding_date = re.search(r'"Doj":"(.*?)"', html_data)

        if not all([boarding_station_name, boarding_station_code, destination_station_name, destination_station_code, boarding_date]):
            missing_fields = {
                "boarding_station_name": bool(boarding_station_name),
                "boarding_station_code": bool(boarding_station_code),
                "destination_station_name": bool(destination_station_name),
                "destination_station_code": bool(destination_station_code),
                "boarding_date": bool(boarding_date)
            }
            logging.error(f"Incomplete data received from the server. Missing fields: {missing_fields}")
            raise ValueError("Incomplete data received from the server.")

        boarding_station_name = boarding_station_name.group(1)
        boarding_station_code = boarding_station_code.group(1)
        destination_station_name = destination_station_name.group(1)
        destination_station_code = destination_station_code.group(1)
        boarding_date = boarding_date.group(1)
        boarding_day = datetime.datetime.strptime(boarding_date, "%d-%m-%Y").strftime("%A")

        departure_time_pattern = r'"DepartureTime":"(\d{2}:\d{2})"'
        arrival_time_pattern = r'"ArrivalTime":"(\d{2}:\d{2})"'

        departure_time_match = re.search(departure_time_pattern, html_data)
        arrival_time_match = re.search(arrival_time_pattern, html_data)

        departure_time = departure_time_match.group(1) if departure_time_match else "N/A"
        arrival_time = arrival_time_match.group(1) if arrival_time_match else "N/A"

        json_data_match = re.search(r'data = ({.*?});', html_data, re.DOTALL)
        passengers_data = []
        if (json_data_match):
            json_data = json.loads(json_data_match.group(1))

            if json_data.get("PassengerStatus"):
                for passenger in json_data["PassengerStatus"]:
                    booking_status = passenger.get("BookingStatus")
                    current_status = passenger.get("CurrentStatus")
                    coach = passenger.get("Coach")
                    booking_berth_no = passenger.get("BookingBerthNo")
                    current_berth_no = passenger.get("CurrentBerthNo")
                    passenger_number = passenger.get("Number")

                    passenger_info = {
                        "passengerNumber": passenger_number,
                        "bookingBerthNo": booking_berth_no.strip(),
                        "bookingStatus": booking_status,
                        "coach": coach,
                        "currentBerthNo": current_berth_no.strip(),
                        "currentStatus": current_status
                    }
                    passengers_data.append(passenger_info)

        return {
            "pnrNumber": pnr_number,
            "trainNumber": train_number,
            "trainName": train_name,
            "boardingStation": f"{boarding_station_name} ({boarding_station_code})",
            "destinationStation": f"{destination_station_name} ({destination_station_code})",
            "boardingDate": f"{boarding_date} ({boarding_day})",
            "departureTime": departure_time,
            "arrivalTime": arrival_time,
            "passengers": passengers_data
        }

    except Exception as e:
        logging.error(f"Error in extract_data: {e}")
        return {"error": str(e)}

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def convert_keys_to_camel_case(data):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            new_key = to_camel_case(k)
            new_dict[new_key] = convert_keys_to_camel_case(v) if isinstance(v, (dict, list)) else v
        return new_dict
    elif isinstance(data, list):
        return [convert_keys_to_camel_case(i) for i in data]
    else:
        return data
