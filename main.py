from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import base64

app = FastAPI(title="Orders API")

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)

# -----------------------------
# Fixed orders catalog
# IDs 1 through 46
# -----------------------------
TOTAL_ORDERS = 46

orders = [
    {
        "id": i,
        "item": f"Order {i}"
    }
    for i in range(1, TOTAL_ORDERS + 1)
]

# -----------------------------
# Idempotency storage
# -----------------------------
idempotency_store = {}

next_order_id = TOTAL_ORDERS + 1

# -----------------------------
# Rate limiting
# 20 requests / 10 seconds
# -----------------------------
RATE_LIMIT = 20
WINDOW = 10

client_requests = {}

# -----------------------------
# Cursor helpers
# -----------------------------
def encode_cursor(position: int) -> str:
    return base64.b64encode(str(position).encode()).decode()


def decode_cursor(cursor: str) -> int:
    try:
        return int(base64.b64decode(cursor).decode())
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid cursor"
        )

# -----------------------------
# Rate limit middleware
# -----------------------------
@app.middleware("http")
async def rate_limit(request: Request, call_next):

    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    if client_id not in client_requests:
        client_requests[client_id] = []

    # Remove timestamps older than 10 seconds
    client_requests[client_id] = [
        t
        for t in client_requests[client_id]
        if now - t < WINDOW
    ]

    # Check limit
    if len(client_requests[client_id]) >= RATE_LIMIT:

        retry_after = WINDOW - (now - client_requests[client_id][0])
        retry_after = max(1, int(retry_after) + 1)

        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "Retry-After": str(retry_after)
            }
        )

    client_requests[client_id].append(now)

    response = await call_next(request)
    return response

# -----------------------------
# Root
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "Orders API is running."
    }

# -----------------------------
# Idempotent POST /orders
# -----------------------------
@app.post("/orders", status_code=201)
def create_order(
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    global next_order_id

    # Same key => return same order
    if idempotency_key in idempotency_store:
        return idempotency_store[idempotency_key]

    new_order = {
        "id": next_order_id,
        "item": "New Order"
    }

    next_order_id += 1

    idempotency_store[idempotency_key] = new_order

    return new_order

# -----------------------------
# GET /orders
# Cursor pagination
# -----------------------------
@app.get("/orders")
def get_orders(
    limit: int = 10,
    cursor: str | None = None
):

    if limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="limit must be greater than 0"
        )

    start = 0

    if cursor:
        start = decode_cursor(cursor)

    if start < 0 or start > len(orders):
        raise HTTPException(
            status_code=400,
            detail="Invalid cursor"
        )

    end = min(start + limit, len(orders))

    items = orders[start:end]

    next_cursor = None

    if end < len(orders):
        next_cursor = encode_cursor(end)

    return {
        "items": items,
        "next_cursor": next_cursor
    }
