from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

# Replace the second origin with your actual exam page origin if provided.
allowed_origins = [
    "https://app-1fzxpn.example.com",
    "https://exam.example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stores request timestamps for each client
clients = {}

# -----------------------------
# Middleware 1: Request Context
# -----------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    # Use existing X-Request-ID or generate a new UUID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    # Save request ID so endpoint can access it
    request.state.request_id = request_id

    # Continue processing request
    response = await call_next(request)

    # Add X-Request-ID to response header
    response.headers["X-Request-ID"] = request_id

    return response


# ---------------------------------
# Middleware 2: Per-client Rate Limit
# ---------------------------------
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    WINDOW = 10  # seconds
    LIMIT = 10   # requests

    history = clients.get(client_id, [])

    # Keep only requests made within last 10 seconds
    history = [t for t in history if now - t < WINDOW]

    # Reject if limit exceeded
    if len(history) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    # Record current request
    history.append(now)
    clients[client_id] = history

    response = await call_next(request)
    return response


# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f2003563@ds.study.iitm.ac.in",  # Replace with your login email
        "request_id": request.state.request_id,
    }
