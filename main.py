from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional

app = FastAPI(title="Idempotency Gateway")

# ===== Data model for request body (so /docs shows JSON input) =====
class PaymentRequest(BaseModel):
    amount: float
    currency: str

# ===== In-memory idempotency store =====
# key -> record
STORE: Dict[str, Dict[str, Any]] = {}
STORE_LOCK = asyncio.Lock()

PROCESSING_SECONDS = 2

# Developer's Choice: TTL expiry to prevent unbounded memory usage
TTL_SECONDS = 60 * 60  # 1 hour


def stable_body_hash(body: Any) -> str:
    """Hash a canonical JSON representation of the body."""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cleanup_expired_keys() -> None:
    now = time.time()
    expired = [k for k, v in STORE.items() if now - v["created_at"] > TTL_SECONDS]
    for k in expired:
        del STORE[k]


@app.get("/")
def root():
    return {"message": "Idempotency Gateway is running"}


@app.post("/process-payment")
async def process_payment(
    payment: PaymentRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    #  Validate header (User Story 1 requirement) 
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    # Convert payment model to dict for hashing/comparison
    body = payment.model_dump()
    req_hash = stable_body_hash(body)

    #  Critical section: check/create record safely (race-safe) 
    async with STORE_LOCK:
        cleanup_expired_keys()

        rec = STORE.get(idempotency_key)

        if rec is None:
            # First time seeing this key -> create IN_FLIGHT record
            done_event = asyncio.Event()
            rec = {
                "hash": req_hash,
                "status": "IN_FLIGHT",   # supports bonus in-flight waiting
                "done": done_event,
                "response_status": None,
                "response_body": None,
                "created_at": time.time(),
            }
            STORE[idempotency_key] = rec
            is_first = True
        else:
            # Key exists -> body must match (User Story 3)
            if rec["hash"] != req_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key already used for a different request body.",
                )
            is_first = False

    # --- Duplicate request path (User Story 2 + Bonus) ---
    if not is_first:
        # If already completed -> return cached response immediately
        if rec["status"] == "COMPLETED":
            resp = JSONResponse(status_code=rec["response_status"], content=rec["response_body"])
            resp.headers["X-Cache-Hit"] = "true"
            return resp

        # If still processing -> wait until first completes (Bonus)
        await rec["done"].wait()
        resp = JSONResponse(status_code=rec["response_status"], content=rec["response_body"])
        resp.headers["X-Cache-Hit"] = "true"
        return resp

    # --- First request path (User Story 1) ---
    await asyncio.sleep(PROCESSING_SECONDS)

    # Response must include: "Charged 100 GHS"
    status_code = 201
    response_body = {"message": f"Charged {payment.amount} {payment.currency}"}

    # Save final result and release any waiters
    async with STORE_LOCK:
        rec["status"] = "COMPLETED"
        rec["response_status"] = status_code
        rec["response_body"] = response_body
        rec["done"].set()

    resp = JSONResponse(status_code=status_code, content=response_body)
    resp.headers["X-Cache-Hit"] = "false"
    return resp