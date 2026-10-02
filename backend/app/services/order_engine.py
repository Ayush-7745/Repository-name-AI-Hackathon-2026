from typing import List, Tuple
from uuid import uuid4

from app.schemas import OrderItem
from app.services.catalog import CatalogService


class OrderEngine:
    def __init__(self, catalog: CatalogService):
        self.catalog = catalog
        self.orders = {}

    def resolve_items(
        self, items: List[OrderItem]
    ) -> Tuple[List[OrderItem], List[str], str | None]:
        resolved = []
        issues = []
        clarification_questions = []

        for item in items:
            search_query = (
                f"{item.brand} {item.product_name}" if item.brand else item.product_name
            )

            candidates = self.catalog.search(
                search_query,
                limit=8,
                brand=item.brand,
                unit=item.pack_unit if item.pack_size is not None else item.unit,
                pack_size=item.pack_size,
            )

            if not candidates:
                issues.append(f"No product found for '{item.product_name}'.")
                clarification_questions.append(
                    f"I couldn't find '{item.product_name}'. Can you choose another product?"
                )
                continue

            # A strong, filtered top result is treated as an exact match.
            # Generic requests with several close results remain ambiguous.
            top_score = float(candidates[0].get("_score", 0))
            close = [c for c in candidates if float(c.get("_score", 0)) >= top_score - 7]

            if len(close) > 1:
                names = [str(c["product_name"]) for c in close[:4]]
                issues.append(f"Ambiguous product: {item.product_name}.")
                clarification_questions.append(
                    "I found multiple matches: " + ", ".join(names) + ". Which one do you want?"
                )
                continue

            product = candidates[0]
            stock = float(product.get("stock") or 0)

            # For packaged variants, quantity means number of packs.
            requested = item.quantity
            if stock <= 0:
                issues.append(f"{product['product_name']} is out of stock.")
                clarification_questions.append(
                    f"{product['product_name']} is out of stock. Would you like another option?"
                )
                continue

            if requested > stock:
                issues.append(
                    f"Only {stock:g} unit(s) of {product['product_name']} are available."
                )
                clarification_questions.append(
                    f"Only {stock:g} unit(s) are available for {product['product_name']}. Would you like that quantity?"
                )
                continue

            resolved.append(
                OrderItem(
                    product_id=str(product["product_id"]),
                    product_name=str(product["product_name"]),
                    quantity=item.quantity,
                    unit=item.unit or (str(product.get("unit")) or None),
                    brand=str(product.get("brand")) or None,
                    pack_size=float(product["pack_size"]) if product.get("pack_size") != "" else None,
                    pack_unit=str(product.get("unit")) or None,
                    price=float(product.get("price") or 0),
                    stock=stock,
                )
            )

        clarification = " ".join(clarification_questions) if clarification_questions else None
        return resolved, issues, clarification

    def confirm(self, items: List[OrderItem]):
        total = round(sum((i.price or 0) * i.quantity for i in items), 2)
        order_id = "ORD-" + uuid4().hex[:8].upper()

        self.orders[order_id] = {
            "order_id": order_id,
            "items": [i.model_dump() for i in items],
            "total": total,
            "status": "CONFIRMED",
        }
        return self.orders[order_id]

    def get(self, order_id: str):
        return self.orders.get(order_id)
