# AI Order Desk - Backend

FastAPI backend for the voice-first Hinglish ordering hackathon MVP.

## Current backend
- Product catalog from `data/indian_kirana_catalog.csv`
- Fuzzy product/brand matching
- Hinglish aliases: atta/aata, chini/sugar, tel/oil, makhan/butter, etc.
- Quantity/unit extraction for common speech patterns
- Ambiguity detection
- Stock validation
- Order confirmation
- Bill endpoint
- Delivery-note endpoint
- Provider-neutral LLM service stub

## Voice architecture
Voice/Chat input -> Speech-to-Text (later) -> `/orders/parse` -> Catalog/Stock -> Clarification -> Confirmation -> Bill

The LLM provider is intentionally isolated so we can plug Gemini or another provider later without rewriting the backend.

## Run on Windows
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health
