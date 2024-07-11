from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST, start_http_server

REQUEST_COUNT = Counter('pnr_status_requests_total', 'Total number of PNR status requests', ['method', 'endpoint', 'http_status'])

def start_prometheus_client(port):
    start_http_server(port)
