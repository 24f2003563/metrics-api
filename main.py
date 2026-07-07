from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

# Replace the second origin with the ACTUAL exam page origin if provided.
allowed_origins = [
    "https://app-1fzxpn.example.com",
    # "https://<actual-exam-origin>"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stores timestamps for each client ID
clients = {}

# -----------------------------
# Middleware 1: Request Context
# -----------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Middleware 2: Rate Limiter
# -----------------------------
@app.middleware("http")
async def rate_limiter(request: Request, call_next):

    # Don't rate-limit CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")

    WINDOW = 10  # seconds
    LIMIT = 10   # requests
    now = time.time()

    history = clients.get(client_id, [])

    # Remove expired timestamps
    history = [t for t in history if now - t < WINDOW]

    if len(history) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    history.append(now)
    clients[client_id] = history

    return await call_next(request)


# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f2003563@ds.study.iitm.ac.in",
        "request_id": request.state.request_id,
    }
