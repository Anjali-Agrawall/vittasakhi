import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads GEMINI_API_KEY from your .env file

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

EXTRACTION_PROMPT = """
You are reading a photo of either (a) a handwritten income/expense ledger
or (b) a UPI payment confirmation screenshot belonging to an informal
woman worker in India.

Extract every transaction you can see into this exact JSON schema:
[
  {
    "date": "YYYY-MM-DD",
    "description": "<short description of the transaction>",
    "amount_inr": <integer>,
    "transaction_type": "income" or "expense",
    "payment_method": "UPI" or "Cash" or "bank_transfer"
  }
]

Rules:
- If a field is not visible or unclear, make your best reasonable guess and do not skip the row.
- Return ONLY the JSON array, no other text, no markdown code fences.
"""


def extract_from_image(image_path: str, max_retries: int = 4) -> list[dict]:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    EXTRACTION_PROMPT,
                ],
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s, 20s
                print(f"  Server busy, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue
            raise  # re-raise any other kind of error immediately

    raise Exception(f"Failed after {max_retries} retries: {image_path}")


if __name__ == "__main__":
    image_dir = "sample_images"
    all_results = {}

    for fname in sorted(os.listdir(image_dir)):
        if not fname.endswith(".jpg"):
            continue
        path = os.path.join(image_dir, fname)
        print(f"Extracting: {fname}")
        try:
            result = extract_from_image(path)
            all_results[fname] = result
            time.sleep(2)  # small pause between calls to avoid rate limits
        except Exception as e:
            print(f"  Error on {fname}: {e}")
            all_results[fname] = {"error": str(e)}

    with open("extraction_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDone. Extracted {len(all_results)} images. Results saved to extraction_results.json")