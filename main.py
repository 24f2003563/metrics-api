from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

allowed_origins = [
    "https://app-1fzxpn.example.com",
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = {}


# -----------------------------
# Request Context Middleware
# -----------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if request_id is None:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # Always echo request ID in response header
    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Rate Limit Middleware
# -----------------------------
@app.middleware("http")
async def rate_limiter(request: Request, call_next):

    # Do not block CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    LIMIT = 10
    WINDOW = 10

    requests = clients.get(client_id, [])

    requests = [
        t for t in requests
        if now - t < WINDOW
    ]

    if len(requests) >= LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

        # Add X-Request-ID even for 429 responses
        response.headers["X-Request-ID"] = request.state.request_id

        return response

    requests.append(now)
    clients[client_id] = requests

    return await call_next(request)


# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f2003563@ds.study.iitm.ac.in",
        "request_id": request.state.request_id
    }
