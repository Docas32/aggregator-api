import uuid

from flask import Flask, Response, request
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

from json_log import get_logger

app = Flask(__name__)

REQUESTS = Counter(
    "http_requests_total", "Requisicoes HTTP totais", ["route", "method", "status"], # labels
)

LATENCY = Histogram(
    "http_request_duration_seconds", "Duracao das requisicoes HTTP em segundos", ["route"],
     buckets=(0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

PENDING_BATCHES = Gauge(
"pending_batches", "Lotes aguardando consolidacao",
)

@app.get("/")
def index():
    return {
        "service": "aggregator-api",
        "endpoints": {
            "batch": "POST /batch",
            "metrics": "GET /metrics",
        },
    }

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)
# formato de texto do Prometheus
@app.post("/batch")
def receive_batch():
    with LATENCY.labels(route="/batch").time():
# cronometra o handler
        try:
            trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
            logger, extra = get_logger(trace_id, "/batch")
            logger.info("Recebendo lote", extra=extra)
            payload = request.get_json(force=True)
            PENDING_BATCHES.inc(len(payload.get("lotes", [])))
            REQUESTS.labels(route="/batch", method="POST", status="200").inc()
            return {"status": "aceito", "lotes": len(payload.get("lotes", []))}
        except Exception:
            REQUESTS.labels(route="/batch", method="POST", status="500").inc()
            return {"status": "erro"}, 500