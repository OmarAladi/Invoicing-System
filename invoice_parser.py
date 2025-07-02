# To run this code you need to install the following dependencies:
# pip install google-genai
# pip install json_repair

import os
import base64
import json
import logging
import json_repair
from typing import List, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ------------------ Logging Setup ------------------ #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("InvoiceParser")

# ------------------ Pydantic Models ------------------ #
# Defines the structure of each product line
class Product(BaseModel):
    Item_ID: str = Field(
        ...,
        min_length=5,
        max_length=12,
        description="The part number or unique identifier for the item listed on the invoice."
    )
    Item_Description: str = Field(
        ...,
        min_length=5,
        description="A textual description of the item, usually including product type and compatibility."
    )
    Unit_Price: float = Field(
        ...,
        description="The price for a single unit of the item, excluding any tax."
    )
    Quantity: int = Field(
        ...,
        description="The number of units of the item purchased."
    )
    Tax: float = Field(
        ...,
        description="The total amount of tax applied to the item."
    )
    Total_Amount: float = Field(
        ...,
        description="The total cost of the item, including tax."
    )

# Structure for invoice-level data
class InvoiceData(BaseModel):
    date: Optional[str] = Field(
        ..., 
        min_length=8, 
        max_length=10, 
        description="Invoice issue date only (DD-MM-YYYY)"
    )
    products: List[Product] = Field(
        [], 
        description="List of products in the invoice"
    )

# Final JSON response structure
class InvoiceResponse(BaseModel):
    data: InvoiceData = Field(...)

# ------------------ Main Class ------------------ #
class InvoiceParser:
    def __init__(self, api_key=None, model="gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.critical("Gemini API key is missing. Aborting initialization.")
            raise ValueError("Gemini API key not provided")
        logger.info("Initializing Gemini client with model: %s", model)
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini client initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize Gemini client.")
            raise e

        self.model = model

    @staticmethod
    def parse_json(text):
        try:
            return json_repair.loads(text)
        except Exception:
            logger.warning("Failed to repair/parse JSON.")
            return None

    # System prompt that defines the expected behavior for the AI model
    def _system_message(self):
        return "\n".join([
            "You are a helpful assistant specialized in extracting structured data from images of Arabic VAT invoices.",
            "The user will provide an image of an invoice. Extract all data and combine into one JSON.",
            
            "Extract for each product: Item_ID, Item_Description, Unit_Price, Quantity, Tax, and Total_Amount.",
            "Also extract the invoice issue date (DD-MM-YYYY)",
            
            "Follow the exact Pydantic schema. Output JSON only — no extra text or explanation.",
            "If invoice is in Arabic, keep all Arabic text and digits as-is."
        ])

    # User prompt that defines the schema for the AI to follow
    def _user_prompt(self):
        return "\n".join([
            ""
        ])
    
    # Main function that sends invoice image(s) to the model and parses response
    def extract_invoice(self, b64_images: List[str]):
        logger.info("Starting invoice extraction for %d image(s)...", len(b64_images))

        # Decode base64-encoded images
        try:
            parts = [
                types.Part.from_bytes(
                    mime_type="image/jpeg", data=base64.b64decode(img_b64)
                )
                for img_b64 in b64_images
            ]
        except Exception as e:
            logger.exception("Failed to decode images. Ensure base64 input is valid.")
            return None

        # Append the user prompt at the end
        parts.append(types.Part.from_text(text=self._user_prompt()))

        contents = [
            types.Content(
                role="user", 
                parts=parts
            )
        ]

        # System instructions + configuration
        generate_content_config = types.GenerateContentConfig(
            temperature=0.2,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="application/json",
            response_schema= InvoiceResponse,
            system_instruction=[
                types.Part.from_text(text=self._system_message()),
            ],
        )

        # Make the API call
        try:
            logger.info("Sending request to Gemini model '%s'...", self.model)
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            logger.info("Gemini API response received.")
        except Exception as e:
            logger.exception("Gemini API call failed.")
            return None

        # Attempt to parse the response JSON
        try:
            logger.debug("Raw response text: %s", response.text[:300])
            json_response = self.parse_json(response.text)
            if not json_response:
                logger.warning("No valid JSON could be parsed from Gemini response.")
                return None
        except Exception as e:
            logger.exception("Exception during parsing JSON from Gemini output.")
            return None

        logger.info("Returning final JSON: %s", json.dumps(json_response, indent=2))
        logger.info("Invoice extraction completed successfully.")

        return json_response

# # ====== للاستخدام مباشرة ======
# parser = InvoiceParser()
# result = parser.extract_invoice(["base"])

# from pprint import pprint
# pprint(result)
