import requests
from bs4 import BeautifulSoup
import json
import re
import datetime
import csv
from fake_useragent import UserAgent

def get_fake_user_agent_response(requests, url):
    try:
        user_agent = UserAgent()
        random_user_agent = user_agent.random
        headers = {"User-Agent": random_user_agent}
        return requests.get(url, headers=headers, timeout=30, verify=False)
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)

def get_data(url):
    response = get_fake_user_agent_response(requests, url)
    return response.text

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
        "Passengers": passengers_data
    }

def write_to_csv(data, filename):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = data.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)

def write_to_json(data, filename):
    with open(filename, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=4)

def main(url):
    html_data = get_data(url)
    extracted_data = extract_data(html_data)

    print("Train Number:", extracted_data["Train Number"])
    print("Train Name:", extracted_data["Train Name"])
    print("Boarding Station:", extracted_data["Boarding Station"])
    print("Destination Station:", extracted_data["Destination Station"])
    print("Boarding Date:", extracted_data["Boarding Date"])

    print("Passengers:")
    for passenger in extracted_data["Passengers"]:
        print(f"   Passenger {passenger['Passenger Number']}:")
        print(f"     - Booking Status: {passenger['Booking Status']}, Coach: {passenger['Coach']}, Berth: {passenger['Booking Berth No']}")
        print(f"     - Current Status: {passenger['Current Status']}, Coach: {passenger['Coach']}, Berth: {passenger['Current Berth No']}")

    # Writing to CSV
    write_to_csv(extracted_data, "pnr_data.csv")
    # Writing to JSON
    write_to_json(extracted_data, "pnr_data.json")

if __name__ == "__main__":
    pnr_number = input("Enter the PNR number: ")
    url = "https://www.confirmtkt.com/pnr-status/" + pnr_number
    main(url)
