from flask import Flask, render_template, request
import requests
import json
import re
import datetime
from fake_useragent import UserAgent
import time
from threading import Lock

app = Flask(__name__)

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
            return requests.get(url, headers=headers, timeout=30, verify=False)
    
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None
    
def get_data(url):
    response = get_fake_user_agent_response(url)
    return response.text if response else ""

def extract_data(html_data):
    train_info_pattern = r'"TrainNo":"(.*?)","TrainName":"(.*?)"'
    train_info_match = re.search(train_info_pattern, html_data)

    if train_info_match:
        train_number = train_info_match.group(1)
        train_name = train_info_match.group(2)
    else:
        train_number = "N/A"
        train_name = "N/A"

    boarding_station_name = re.search(r'"BoardingStationName":"(.*?)"', html_data).group(1)
    boarding_station_code = re.search(r'"From":"(.*?)"', html_data).group(1)
    destination_station_name = re.search(r'"ReservationUptoName":"(.*?)"', html_data).group(1)
    destination_station_code = re.search(r'"To":"(.*?)"', html_data).group(1)
    boarding_date = re.search(r'"Doj":"(.*?)"', html_data).group(1)
    boarding_day = datetime.datetime.strptime(boarding_date, "%d-%m-%Y").strftime("%A")

    departure_time_pattern = r'"DepartureTime":"(\d{2}:\d{2})"'
    arrival_time_pattern = r'"ArrivalTime":"(\d{2}:\d{2})"'

    departure_time_match = re.search(departure_time_pattern, html_data)
    arrival_time_match = re.search(arrival_time_pattern, html_data)

    departure_time = departure_time_match.group(1) if departure_time_match else "N/A"
    arrival_time = arrival_time_match.group(1) if arrival_time_match else "N/A"

    json_data_match = re.search(r'data = ({.*?});', html_data, re.DOTALL)
    passengers_data = []
    if json_data_match:
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
                    "Passenger Number": passenger_number,
                    "Booking Status": booking_status,
                    "Current Status": current_status,
                    "Coach": coach,
                    "Booking Berth No": booking_berth_no,
                    "Current Berth No": current_berth_no
                }
                passengers_data.append(passenger_info)

    return {
        "Train Number": train_number,
        "Train Name": train_name,
        "Boarding Station": f"{boarding_station_name} ({boarding_station_code})",
        "Destination Station": f"{destination_station_name} ({destination_station_code})",
        "Boarding Date": f"{boarding_date} ({boarding_day})",
        "Departure Time": departure_time,
        "Arrival Time": arrival_time,
        "Passengers": passengers_data
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    error_message = None
    extracted_data = None
    if request.method == 'POST':
        pnr_number = request.form['pnr']
        if re.match(r'^\d{10}$', pnr_number):
            url = f"https://www.confirmtkt.com/pnr-status/{pnr_number}"
            html_data = get_data(url)
            extracted_data = extract_data(html_data)
            extracted_data['PNR Number'] = pnr_number
        else:
            error_message = "Enter the correct format 10 digit PNR number"

    return render_template('index.html', data=extracted_data, error=error_message)

#if __name__ == "__main__":
 #   app.run(debug=True)