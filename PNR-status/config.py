import os

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://example-frontend.com,https://another-frontend.com").split(",")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 8000))
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
RATE_LIMIT = os.getenv("RATE_LIMIT", "120 per minute")
