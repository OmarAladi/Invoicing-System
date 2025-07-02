# pip install fastapi uvicorn

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from invoice_parser import InvoiceParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

parser = InvoiceParser()
app = FastAPI()

class ImagesRequest(BaseModel):
    image: str

@app.post("/api/multiple-invoice")
def process_invoice(request: ImagesRequest):
    b64_image = request.image.split(",")[-1] if "," in request.image else request.image

    try:
        invoice_data = parser.extract_invoice([b64_image])
        if not invoice_data:
            raise HTTPException(status_code=500, detail="Invoice processing failed")
        return invoice_data
    except Exception as e:
        logging.exception("An error occurred during processing invoices in endpoint.")
        raise HTTPException(status_code=500, detail="Internal server error")

# uvicorn api:app --reload
