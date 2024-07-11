import http.client

pnr_numbers = [
    "2758593543", "2761981310", "6134979034", "2758593543", "4910024233",
    "4164403703", "4200665257", "2313446108", "6134863748", "4820522864",
    "2861910669", "6534551448", "6235931548", "6735889710", "6536038402"
]

def fetch_pnr_status(pnr_number):
    conn = http.client.HTTPSConnection("pnr-status10.p.rapidapi.com")

    payload = "{\"pnr\":\"" + pnr_number + "\"}"

    headers = {
        'x-rapidapi-key': "4e8eeae445mshc467740ff3d0747p18e7ccjsn98d131ea3b45",
        'x-rapidapi-host': "pnr-status10.p.rapidapi.com",
        'Content-Type': "application/json"
    }

    conn.request("POST", "/api/pnr-status", payload, headers)

    res = conn.getresponse()
    data = res.read()

    print("PNR Number:", pnr_number)
    print("Response:", data.decode("utf-8"))
    print("-----------------------")

for pnr_number in pnr_numbers:
    fetch_pnr_status(pnr_number)
