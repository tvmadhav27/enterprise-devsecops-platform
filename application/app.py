from flask import Flask, jsonify, Response, request, g
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "abc_retail_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "abc_retail_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"]
)

@app.before_request
def start_timer():
    if request.path != "/metrics":
        g.start_time = time.time()

@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        endpoint = request.endpoint or "unknown"
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()

        duration = time.time() - getattr(g, "start_time", time.time())
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

    return response

@app.route("/")
def home():
    return jsonify({
        "application": "ABC Retail",
        "status": "healthy",
        "version": "1.0.0"
    })

@app.route("/health")
def health():
    return jsonify({"status": "UP"}), 200

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
