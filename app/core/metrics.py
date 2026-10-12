from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "pretium_requests_total", "Total requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "pretium_request_latency_seconds", "Request latency", ["method", "path"]
)
INGESTION_CHANGES = Counter(
    "pretium_ingestion_changes_total", "Price changes detected per source", ["source"]
)


def metrics_body() -> bytes:
    return generate_latest()
