from fastapi import FastAPI, Header, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
import base64
import time

app = FastAPI(title="Orders API")

# -----------------------------
# Enable CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Fixed catalog of orders (1-46)
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
next_order_id = 1000

# -----------------------------
# Rate limit storage
# -----------------------------
RATE_LIMIT = 20          # requests
WINDOW = 10              # seconds

client_requests = {}


# ==========================================================
# Rate Limiter
# ==========================================================
def check_rate_limit(client_id: str):
    now = time.time()

    timestamps = client_requests.get(client_id, [])

    # Keep only requests made in the last 10 seconds
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        retry_after = WINDOW - (now - timestamps[0])

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(max(1, int(retry_after)))
            }
        )

    timestamps.append(now)
    client_requests[client_id] = timestamps


# ==========================================================
# POST /orders
# Idempotent order creation
# ==========================================================
@app.post("/orders", status_code=201)
def create_order(
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    client_id: str = Header(..., alias="X-Client-Id")
):
    global next_order_id

    check_rate_limit(client_id)

    # If key already exists, return same order
    if idempotency_key in idempotency_store:
        response.status_code = 201
        return idempotency_store[idempotency_key]

    # Create new order
    order = {
        "id": next_order_id,
        "item": "New Order"
    }

    next_order_id += 1

    idempotency_store[idempotency_key] = order

    return order


# ==========================================================
# GET /orders
# Cursor Pagination
# ==========================================================
@app.get("/orders")
def get_orders(
    limit: int = Query(10, gt=0),
    cursor: str | None = None,
    client_id: str = Header(..., alias="X-Client-Id")
):

    check_rate_limit(client_id)

    # Decode cursor
    if cursor is None:
        start = 0
    else:
        try:
            start = int(base64.b64decode(cursor.encode()).decode())
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    end = min(start + limit, len(orders))

    page = orders[start:end]

    if end >= len(orders):
        next_cursor = None
    else:
        next_cursor = base64.b64encode(str(end).encode()).decode()

    return {
        "items": page,
        "next_cursor": next_cursor
    }


# ==========================================================
# Health Check
# ==========================================================
@app.get("/")
def root():
    return {
        "message": "Orders API is running"
    }
