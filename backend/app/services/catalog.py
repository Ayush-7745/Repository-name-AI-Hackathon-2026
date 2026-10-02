from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from rapidfuzz import fuzz

from app.config import CATALOG_FILE


class CatalogService:
    def __init__(self, path: Path = CATALOG_FILE):
        self.path = path
        self.df = pd.read_csv(path).fillna("")
        for col in ["product_name", "brand", "category", "sub_category", "aliases", "unit"]:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str)

    def search(
        self,
        query: str,
        limit: int = 10,
        brand: Optional[str] = None,
        unit: Optional[str] = None,
        pack_size: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        q = query.lower().strip()
        work = self.df.copy()

        if brand:
            b = brand.lower().strip()
            work = work[work["brand"].str.lower().eq(b)]

        if unit:
            u = unit.lower()
            compatible = work["unit"].str.lower().eq(u)
            work = work[compatible | work["unit"].eq("")]

        if pack_size is not None:
            def size_match(v):
                try:
                    return float(v) == float(pack_size)
                except (TypeError, ValueError):
                    return False
            work = work[work["pack_size"].map(size_match)]

        scored = []
        for _, row in work.iterrows():
            product = str(row["product_name"]).lower()
            aliases = str(row["aliases"]).lower()
            row_brand = str(row["brand"]).lower()

            product_score = fuzz.token_set_ratio(q, product)
            alias_score = fuzz.token_set_ratio(q, aliases)
            score = max(product_score, alias_score)

            if q and q in product:
                score += 25

            if brand and row_brand == brand.lower():
                score += 20

            item = row.to_dict()
            item["_score"] = round(float(score), 2)
            if score >= 45:
                scored.append(item)

        scored.sort(key=lambda x: x["_score"], reverse=True)
        return scored[:limit]

    def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        match = self.df[self.df["product_id"].astype(str) == str(product_id)]
        if match.empty:
            return None
        return match.iloc[0].to_dict()
