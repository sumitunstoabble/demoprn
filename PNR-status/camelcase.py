import requests

url = "http://127.0.0.1:5000/api/v1/train_status"
data = {
    "trainNumber": "14722"
}

response = requests.post(url, json=data)

try:
    response_json = response.json()
except requests.exceptions.JSONDecodeError:
    print("Response is not in JSON format or is empty")
    print(response.text)
else:
    print(response_json)
