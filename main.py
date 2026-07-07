from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import time
import uuid

app = FastAPI()

# Record application startup time
startup_time = time.time()

# Prometheus Counter
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# Store logs in memory
logs = []


@app.middleware("http")
async def log_and_count_requests(request: Request, call_next):
    """
    Runs before every request.
    Increments the Prometheus counter and stores a JSON log entry.
    """

    # Increment request counter
    http_requests_total.inc()

    # Create log entry
    log_entry = {
        "level": "INFO",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "path": request.url.path,
        "request_id": str(uuid.uuid4())
    }

    logs.append(log_entry)

    # Keep only last 1000 logs (optional)
    if len(logs) > 1000:
        logs.pop(0)

    response = await call_next(request)
    return response


@app.get("/")
def home():
    return {
        "message": "Production Observability API"
    }


@app.get("/work")
def work(n: int = 1):
    """
    Simulate doing n units of work.
    """

    # Fake work
    for _ in range(n):
        pass

    return {
        "email": "your_email@example.com",   # Replace with your email
        "done": n
    }


@app.get("/metrics")
def metrics():
    """
    Expose Prometheus metrics.
    """
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/healthz")
def healthz():
    """
    Health check endpoint.
    """
    uptime = time.time() - startup_time

    return {
        "status": "ok",
        "uptime_s": uptime
    }


@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    """
    Return the last N log entries.
    """
    if limit < 1:
        limit = 1

    return logs[-limit:]
