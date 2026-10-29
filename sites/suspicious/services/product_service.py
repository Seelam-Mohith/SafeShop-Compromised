"""Product data helpers shared by the simulated storefront.

Reuses the same fictional product dataset as the legitimate ShopSafe baseline.
"""

import json
import os


def load_products(data_path=None):
    if data_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        data_path = os.path.join(base_dir, "data", "products.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_product_by_id(products, product_id):
    try:
        pid = int(product_id)
    except (ValueError, TypeError):
        return None
    for p in products:
        if p.get("id") == pid:
            return p
    return None


def get_products_by_category(products, category_name):
    category = (category_name or "").strip()
    if not category:
        return []
    return [
        p for p in products
        if p.get("category", "").lower() == category.lower()
    ]
