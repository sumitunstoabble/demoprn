from flask import Flask, jsonify, request, redirect, url_for
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv
import os

from config import CORS_ORIGINS, PROMETHEUS_PORT, RATE_LIMIT
from routes import create_pnr_status_routes
from logging_config import setup_logging

load_dotenv()
setup_logging()

app = Flask(__name__)

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "PNR Status API",
        "description": "API for retrieving PNR status",
        "version": "1.0.0"
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)

CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["120 per minute"]
)

# Register Blueprints
pnr_status_blueprint = create_pnr_status_routes(limiter)
app.register_blueprint(pnr_status_blueprint, url_prefix='/api')

@app.route('/')
def home():
    return redirect(url_for('flasgger.apidocs'))

@app.errorhandler(500)
def internal_error(e):
    from metrics import REQUEST_COUNT
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path, http_status=500).inc()
    return jsonify({"error": "An internal server error occurred. Please try again later."}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
