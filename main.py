from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest
import time
import uuid
from datetime import datetime


app = FastAPI()


# Count every request
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests"
)


# Store logs in memory
logs = []


# Remember when the server started
START_TIME = time.time()



@app.middleware("http")
async def log_requests(request: Request, call_next):

    request_id = str(uuid.uuid4())

    response = await call_next(request)

    REQUEST_COUNT.inc()


    log_entry = {
        "level": "INFO",
        "ts": datetime.utcnow().isoformat(),
        "path": request.url.path,
        "request_id": request_id
    }

    logs.append(log_entry)


    # Keep only latest 100 logs
    if len(logs) > 100:
        logs.pop(0)


    return response



@app.get("/work")
def work(n: int = 1):

    # Simulate doing work
    total = 0

    for i in range(n):
        total += i


    return {
        "email": "student@example.com",
        "done": n
    }



@app.get("/metrics")
def metrics():

    return PlainTextResponse(
        generate_latest()
    )



@app.get("/healthz")
def health():

    uptime = time.time() - START_TIME

    return {
        "status": "ok",
        "uptime_s": uptime
    }



@app.get("/logs/tail")
def tail_logs(limit: int = 10):

    return logs[-limit:]
