from fastapi import FastAPI, Header, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64
import time

app = FastAPI(title="Orders API")

# -------------------------------------------------
# CORS
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Assignment values
# -------------------------------------------------
TOTAL_ORDERS = 46
RATE_LIMIT = 20
WINDOW = 10

# Fixed catalog: IDs 1..46
orders = [{"id": i, "item": f"Order {i}"} for i in range(1, TOTAL_ORDERS + 1)]

# Idempotency store
idempotency_store = {}
next_order_id = 1000

# Rate limiter store
client_requests = {}


# -------------------------------------------------
# Rate limiter
# -------------------------------------------------
from fastapi.responses import Response

def rate_limit(client_id: str):
    now = time.time()

    timestamps = client_requests.get(client_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        return Response(
            content='{"detail":"Rate limit exceeded"}',
            status_code=429,
            media_type="application/json",
            headers={
                "Retry-After": "10"
            }
        )

    timestamps.append(now)
    client_requests[client_id] = timestamps
    return None


# -------------------------------------------------
# Health check
# -------------------------------------------------
@app.get("/")
def root():
    return {"status": "running"}


# -------------------------------------------------
# POST /orders
# -------------------------------------------------
@app.post("/orders", status_code=201)
def create_order(
    response: Response,
    client_id: str = Header(..., alias="X-Client-Id"),
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    global next_order_id

    limited = rate_limit(client_id)
    if limited:
        return limited

    # Same key => same order
    if idempotency_key in idempotency_store:
        response.status_code = 201
        return idempotency_store[idempotency_key]

    order = {
        "id": next_order_id,
        "item": "New Order"
    }

    next_order_id += 1

    idempotency_store[idempotency_key] = order

    return order


# -------------------------------------------------
# GET /orders
# -------------------------------------------------
@app.get("/orders")
def list_orders(
    limit: int = Query(..., gt=0),
    cursor: str | None = None,
    client_id: str = Header(..., alias="X-Client-Id")
):
    limited = rate_limit(client_id)
    if limited:
        return limited

    if cursor:
        try:
            start = int(base64.b64decode(cursor).decode())
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid cursor"}
            )
    else:
        start = 0

    end = min(start + limit, TOTAL_ORDERS)

    items = orders[start:end]

    if end >= TOTAL_ORDERS:
        next_cursor = None
    else:
        next_cursor = base64.b64encode(str(end).encode()).decode()

    return {
        "items": items,
        "next_cursor": next_cursor
    }
