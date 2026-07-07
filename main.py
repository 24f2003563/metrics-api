from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

# Allowed origins
allowed_origins = [
    "https://app-1fzxpn.example.com",
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Store timestamps for each client
client_requests = {}

# Single middleware for Request ID + Rate Limiting
@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    # -----------------------------
    # Request Context
    # -----------------------------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # -----------------------------
    # Rate Limiting
    # -----------------------------
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    if client_id not in client_requests:
        client_requests[client_id] = []

    # Keep only requests from the last 10 seconds
    client_requests[client_id] = [
        t for t in client_requests[client_id]
        if now - t < 10
    ]

    # Limit: 10 requests / 10 seconds
    if len(client_requests[client_id]) >= 10:
        response = JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "request_id": request_id,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response

    client_requests[client_id].append(now)

    # Continue to endpoint
    response = await call_next(request)

    # Echo Request ID in response header
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f2003563@ds.study.iitm.ac.in",
        "request_id": request.state.request_id,
    }
