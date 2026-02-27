from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Optional

app = FastAPI()

class PaymentRequest(BaseModel):
    amount: float
    currency: str

@app.get("/")
def root():
    return {"message": "Idempotency Gateway is running"}

@app.post("/process-payment")
async def process_payment(
    payment: PaymentRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    await asyncio.sleep(2)
    return {"message": f"Charged {payment.amount} {payment.currency}"}