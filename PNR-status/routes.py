from flask import Blueprint, request, jsonify
import re

from utils import get_data, extract_data, convert_keys_to_camel_case
from metrics import REQUEST_COUNT

pnr_status_blueprint = Blueprint('pnr_status', __name__)

def create_pnr_status_routes(limiter):
    @pnr_status_blueprint.route('/pnr-status', methods=['POST'])
    @limiter.limit("120 per minute")
    def pnr_status():
        """
        PNR Status
        ---
        tags:
          - PNR
        parameters:
          - name: body
            in: body
            required: true
            schema:
              id: PNRStatus
              properties:
                pnr:
                  type: string
                  description: The PNR number
                  example: "1234567890"
        responses:
          200:
            description: PNR status retrieved
            schema:
              id: PNRStatusResponse
              properties:
                trainNumber:
                  type: string
                trainName:
                  type: string
                boardingStation:
                  type: string
                destinationStation:
                  type: string
                boardingDate:
                  type: string
                departureTime:
                  type: string
                arrivalTime:
                  type: string
                passengers:
                  type: array
                  items:
                    schema:
                      id: PassengerStatus
                      properties:
                        passengerNumber:
                          type: integer
                        bookingBerthNo:
                          type: string
                        bookingStatus:
                          type: string
                        coach:
                          type: string
                        currentBerthNo:
                          type: string
                        currentStatus:
                          type: string
        """
        try:
            data = request.get_json(force=True)
            pnr_number = data.get('pnr')
            if not pnr_number or not re.match(r'^\d{10}$', pnr_number):
                REQUEST_COUNT.labels(method='POST', endpoint='/api/pnr-status', http_status=400).inc()
                return jsonify({"error": "Invalid PNR format. It must be a 10-digit number."}), 400
            
            url = f"https://www.confirmtkt.com/pnr-status/{pnr_number}"
            html_data, error = get_data(url)
            if error:
                REQUEST_COUNT.labels(method='POST', endpoint='/api/pnr-status', http_status=500).inc()
                return jsonify({"error": error}), 500
            if not html_data:
                REQUEST_COUNT.labels(method='POST', endpoint='/api/pnr-status', http_status=500).inc()
                return jsonify({"error": "Failed to retrieve data from the server"}), 500
            
            extracted_data = extract_data(html_data, pnr_number)
            if "error" in extracted_data:
                REQUEST_COUNT.labels(method='POST', endpoint='/api/pnr-status', http_status=500).inc()
                return jsonify({"error": extracted_data["error"]}), 500

            extracted_data['pnrNumber'] = pnr_number
            camel_case_data = convert_keys_to_camel_case(extracted_data)
            REQUEST_COUNT.labels(method='POST', endpoint='/api/pnr-status', http_status=200).inc()
            return jsonify(camel_case_data)
        except Exception as e:
            REQUEST_COUNT.labels(method='POST', endpoint='/api/pnr-status', http_status=500).inc()
            return jsonify({"error": str(e)}), 500

    return pnr_status_blueprint
