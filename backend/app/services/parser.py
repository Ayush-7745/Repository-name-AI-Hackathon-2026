import re
from typing import List, Optional, Tuple

from app.schemas import OrderItem


NUMBER_WORDS = {
    "ek": 1, "one": 1, "do": 2, "two": 2, "teen": 3, "three": 3,
    "char": 4, "four": 4, "paanch": 5, "five": 5, "chhe": 6, "six": 6,
    "saat": 7, "seven": 7, "aath": 8, "eight": 8, "nau": 9, "nine": 9,
    "das": 10, "ten": 10,
}

UNIT_WORDS = {
    "kilo": "kg", "kg": "kg", "kgs": "kg",
    "gram": "g", "grams": "g", "gm": "g", "g": "g",
    "litre": "L", "liter": "L", "liters": "L", "l": "L",
    "ml": "ml", "packet": "pack", "packets": "pack", "pack": "pack",
    "bottle": "bottle", "bottles": "bottle",
}

ALIASES = {
    "aata": "atta",
    "chini": "sugar",
    "chinni": "sugar",
    "namak": "salt",
    "tel": "oil",
    "makhan": "butter",
    "chawal": "rice",
    "doodh": "milk",
    "dahi": "curd",
    "chai patti": "tea",
    "biscit": "biscuit",
    "ande": "eggs",
    "andey": "eggs",
}

COMMON_BRANDS = [
    "tata sampann", "surf excel", "aashirvaad", "fortune", "amul",
    "tata", "saffola", "parle", "maggi", "dabur", "everest", "mdh",
    "harpic", "colgate", "patanjali", "britannia", "haldiram"
]

PRODUCT_TERMS = [
    "sunflower oil", "mustard oil", "rice bran oil", "toor dal", "moong dal",
    "chana dal", "garam masala", "chana masala", "parle-g", "parle g",
    "surf excel", "maggi", "butter", "atta", "sugar", "oil", "rice", "dal",
    "salt", "biscuit", "tea", "coffee", "milk", "curd", "paneer", "ghee",
    "honey", "masala", "water", "eggs", "onion", "potato", "tomato", "harpic",
    "colgate"
]


def normalize_text(text: str) -> str:
    s = text.lower().strip()
    for src, dst in sorted(ALIASES.items(), key=lambda x: -len(x[0])):
        s = s.replace(src, dst)
    return re.sub(r"\s+", " ", s)


def extract_amount_unit(text: str) -> Tuple[Optional[float], Optional[str]]:
    s = text.lower()

    m = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(kg|kgs|kilo|g|gm|gram|grams|l|litre|liter|ml|packet|packets|pack|bottle|bottles)?\b",
        s
    )
    if m:
        amount = float(m.group(1))
        raw_unit = m.group(2)
        return amount, UNIT_WORDS.get(raw_unit) if raw_unit else None

    if "aadha" in s or "half" in s:
        return 0.5, parse_unit(s)

    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", s):
            return float(value), parse_unit(s)

    return None, None


def parse_unit(text: str):
    for word, unit in UNIT_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", text.lower()):
            return unit
    return None


def extract_brand(text: str) -> Optional[str]:
    s = text.lower()
    for brand in sorted(COMMON_BRANDS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(brand)}\b", s):
            return "MDH" if brand == "mdh" else brand.title()
    return None


def extract_product(text: str) -> Optional[str]:
    s = text.lower()
    for term in sorted(PRODUCT_TERMS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(term)}\b", s):
            return "parle-g" if term == "parle g" else term
    return None


def parse_message(message: str) -> List[OrderItem]:
    s = normalize_text(message)
    chunks = re.split(r"\s*(?:,|\band\b|\baur\b)\s*", s)
    items: List[OrderItem] = []

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        product = extract_product(chunk)
        brand = extract_brand(chunk)

        if not product and brand:
            product = brand.lower()

        if not product:
            continue

        amount, unit = extract_amount_unit(chunk)

        # When a branded packaged product includes "500g / 1L / 5kg",
        # interpret that as the pack size and quantity=1.
        # Generic requests such as "2 kilo atta" remain quantity-based.
        is_packaged_brand_request = (
            brand is not None
            and amount is not None
            and unit in {"g", "kg", "L", "ml"}
        )

        if is_packaged_brand_request:
            quantity = 1.0
            pack_size = amount
            pack_unit = unit
        else:
            quantity = amount if amount is not None else 1.0
            pack_size = None
            pack_unit = None

        items.append(
            OrderItem(
                product_name=product,
                quantity=quantity,
                unit=unit,
                brand=brand,
                pack_size=pack_size,
                pack_unit=pack_unit,
            )
        )

    return items
