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


# Request Context Middleware
@app.middleware("http")
async def request_context(request: Request, call_next):

    # Read incoming X-Request-ID
    request_id = request.headers.get("X-Request-ID")

    # Generate if missing
    if not request_id:
        request_id = str(uuid.uuid4())

    # Save for endpoint
    request.state.request_id = request_id

    response = await call_next(request)

    # Echo same ID back in response header
    response.headers["X-Request-ID"] = request_id

    return response


# Rate Limiter Middleware
@app.middleware("http")
async def rate_limiter(request: Request, call_next):

    # Allow CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    WINDOW = 10
    LIMIT = 10

    history = clients.get(client_id, [])

    history = [
        timestamp
        for timestamp in history
        if now - timestamp < WINDOW
    ]

    if len(history) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    history.append(now)
    clients[client_id] = history

    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": "24f2003563@ds.study.iitm.ac.in",
        "request_id": request.state.request_id,
    }
