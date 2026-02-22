"""
Mapper module for Trans.eu offers.
Converts raw dictionary data from parser into normalized domain structures.
"""
from typing import Dict, Any, Optional
import re
from datetime import datetime

def map_to_cargo(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps raw extracted data to a normalized Cargo dict (DTO compatible).
    """
    
    # 1. Price Normalization
    price_raw = raw_data.get("price_raw", "")
    price, currency = _parse_price(price_raw)
    
    # 2. Distance
    dist_raw = raw_data.get("distance_raw", "")
    distance_km = _parse_distance(dist_raw)

    # 3. Dates (Simple pass-through or basic parsing)
    # Parsing dates requires specific format knowledge, passing raw for now if format unknown
    
    # 4. Cargo Body/Weight parsing from "cargo_info_raw"
    body_type, weight = _parse_cargo_info(raw_data.get("cargo_info_raw", ""))

    return {
        "external_id": raw_data.get("external_id"),
        "source": "trans.eu",
        "loading_place": {
            "raw": raw_data.get("loading_place_raw"),
            # City/Zip/Country extraction would go here
        },
        "unloading_place": {
            "raw": raw_data.get("unloading_place_raw"),
        },
        "loading_date_raw": raw_data.get("loading_date_raw"),
        "unloading_date_raw": raw_data.get("unloading_date_raw"),
        "body_type": body_type,
        "weight": weight,
        "price": price,
        "currency": currency,
        "distance_trans_eu": distance_km,
        "company_name": raw_data.get("company_name"),
        "raw_data": raw_data # Keep raw validation
    }

def _parse_price(price_str: Optional[str]):
    if not price_str:
        return None, "EUR"
    
    # Remove whitespace
    clean = price_str.replace(" ", "").upper()
    
    # Extract number
    currency = "EUR"
    amount = 0.0
    
    if "EUR" in clean or "€" in clean:
        currency = "EUR"
    elif "PLN" in clean:
        currency = "PLN" # Mapper should ideally convert, but we need rates. keeping normalized currency code.
    
    # Simple regex for number
    match = re.search(r'[\d\.,]+', clean)
    if match:
        num_str = match.group(0).replace(",", ".")
        try:
            amount = float(num_str)
        except ValueError:
            pass
            
    return amount, currency

def _parse_distance(dist_str: Optional[str]) -> Optional[int]:
    if not dist_str:
        return None
    
    # "123 km"
    match = re.search(r'(\d+)', dist_str.replace(" ", ""))
    if match:
        return int(match.group(1))
    return None

def _parse_cargo_info(info_str: Optional[str]):
    # e.g. "24t, Curtain, 13.6 ldm"
    if not info_str:
        return None, None
        
    weight = None
    body = info_str
    
    # Try to extract weight "24 t" or "24t"
    w_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*t', info_str, re.IGNORECASE)
    if w_match:
        try:
            weight = float(w_match.group(1).replace(",", ".")) * 1000 # to kg? spec says float(kg)? Check spec.
            # Spec says "weight: Float (kg)". 2.4 Entity Cargo.
        except:
            pass
            
    return body, weight
