from fastapi import FastAPI
from pydantic import BaseModel
import ollama
import json
import re

app = FastAPI(title="Invoice Extraction API")


# Request Model
class ExtractRequest(BaseModel):
    text: str


# Response Model
class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: ExtractRequest):
    # Handle empty input
    if not req.text.strip():
        return InvoiceResponse(
            vendor="",
            amount=0.0,
            currency="",
            date=""
        )

    prompt = f"""
You are an invoice information extraction system.

Extract these fields from the invoice text.

Return ONLY valid JSON.

Schema:

{{
  "vendor": "string",
  "amount": number,
  "currency": "USD",
  "date": "YYYY-MM-DD"
}}

Rules:
- vendor = company issuing the invoice
- amount = total amount due
- currency = 3-letter uppercase code
- date = payment due date in YYYY-MM-DD format
- Do not include explanations.
- Output ONLY JSON.

Invoice Text:

{req.text}
"""

    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        reply = response["message"]["content"].strip()

        # Remove Markdown code fences if present
        reply = re.sub(r"```json|```", "", reply).strip()

        data = json.loads(reply)

        vendor = str(data.get("vendor", "")).strip()

        try:
            amount = float(data.get("amount", 0))
        except Exception:
            amount = 0.0

        currency = str(data.get("currency", "")).upper().strip()

        date = str(data.get("date", "")).strip()

        return InvoiceResponse(
            vendor=vendor,
            amount=amount,
            currency=currency,
            date=date,
        )

    except Exception:
        # Never return HTTP 500 because of parsing/model issues
        return InvoiceResponse(
            vendor="",
            amount=0.0,
            currency="",
            date=""
        )


@app.get("/")
def root():
    return {
        "message": "Invoice Extraction API is running."
    }
