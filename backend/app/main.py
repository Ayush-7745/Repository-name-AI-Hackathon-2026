from fastapi import FastAPI, HTTPException

from app.schemas import (
    ParseRequest, ParseResponse,
    ValidateRequest, ValidateResponse,
    ConfirmRequest, ConfirmResponse,
)
from app.services.catalog import CatalogService
from app.services.parser import parse_message
from app.services.order_engine import OrderEngine
from app.services.llm import LLMService

app = FastAPI(
    title="AI Order Desk Backend",
    version="0.1.0",
    description="Voice-first Hinglish order processing backend for the hackathon.",
)

catalog = CatalogService()
engine = OrderEngine(catalog)
llm = LLMService()


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-order-desk-backend"}


@app.get("/products/search")
def product_search(q: str, limit: int = 10):
    return {"query": q, "results": catalog.search(q, limit=limit)}


@app.post("/orders/parse", response_model=ParseResponse)
def parse_order(req: ParseRequest):
    items = parse_message(req.message)
    if not items:
        return ParseResponse(
            message=req.message,
            items=[],
            clarification_needed=True,
            clarification_question="I could not identify a product. Please tell me what you would like to order.",
        )

    resolved, issues, clarification = engine.resolve_items(items)

    return ParseResponse(
        message=req.message,
        items=resolved,
        clarification_needed=bool(issues),
        clarification_question=llm.generate_clarification(clarification) if clarification else None,
    )


@app.post("/orders/validate", response_model=ValidateResponse)
def validate_order(req: ValidateRequest):
    resolved, issues, clarification = engine.resolve_items(req.items)
    return ValidateResponse(
        items=resolved,
        clarification_needed=bool(issues),
        clarification_question=clarification,
        issues=issues,
    )


@app.post("/orders/confirm", response_model=ConfirmResponse)
def confirm_order(req: ConfirmRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cannot confirm an empty order.")

    result = engine.confirm(req.items)
    return result


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = engine.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


@app.get("/orders/{order_id}/bill")
def get_bill(order_id: str):
    order = engine.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    return {
        "order_id": order_id,
        "items": order["items"],
        "total": order["total"],
        "status": order["status"],
    }


@app.get("/orders/{order_id}/delivery-note")
def get_delivery_note(order_id: str):
    order = engine.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    return {
        "order_id": order_id,
        "status": order["status"],
        "items": [
            {
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit": item["unit"],
            }
            for item in order["items"]
        ],
        "message": "Order ready for delivery.",
    }
