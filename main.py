from fastapi import FastAPI, Header, Request, Response, HTTPException
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)


# -----------------------------
# Fixed orders catalog
# IDs 1 to 46
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


# -----------------------------
# Rate limiter
# 20 requests / 10 seconds
# -----------------------------
RATE_LIMIT = 20
WINDOW = 10

client_requests = {}


# -----------------------------
# Cursor helpers
# -----------------------------
def encode_cursor(position: int):
    return base64.b64encode(
        str(position).encode()
    ).decode()


def decode_cursor(cursor: str):
    try:
        return int(
            base64.b64decode(cursor).decode()
        )
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

    client_id = request.headers.get(
        "X-Client-Id",
        "anonymous"
    )

    now = time.time()

    if client_id not in client_requests:
        client_requests[client_id] = []


    # Remove old requests
    client_requests[client_id] = [
        timestamp
        for timestamp in client_requests[client_id]
        if now - timestamp < WINDOW
    ]


    # Check limit
    if len(client_requests[client_id]) >= RATE_LIMIT:
        return Response(
            content="Rate limit exceeded",
            status_code=429,
            headers={
                "Retry-After": "10"
            }
        )


    # Store request time
    client_requests[client_id].append(now)


    response = await call_next(request)

    return response



# -----------------------------
# Root endpoint
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "Orders API is running."
    }



# -----------------------------
# Idempotent order creation
# -----------------------------
@app.post("/orders")
def create_order(
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key"
    )
):

    # Same key => same order
    if idempotency_key in idempotency_store:
        return JSONResponse(
            status_code=201,
            content=idempotency_store[idempotency_key]
        )


    new_order = {
        "id": len(orders) + 1,
        "item": "New Order"
    }


    idempotency_store[idempotency_key] = new_order


    return JSONResponse(
        status_code=201,
        content=new_order
    )



# -----------------------------
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
            detail="limit must be greater than zero"
        )


    start = 0


    if cursor:
        start = decode_cursor(cursor)


    end = start + limit


    items = orders[start:end]


    next_cursor = None

    if end < len(orders):
        next_cursor = encode_cursor(end)


    return {
        "items": items,
        "next_cursor": next_cursor
    }
