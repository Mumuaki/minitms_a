"""
Mapper module for Trans.eu offers.
Converts raw dictionary data from parser into normalized domain structures.
"""
from typing import Dict, Any, Optional
import re
import json
from datetime import datetime

FORBIDDEN_EQUIPMENT_KEYWORDS = [
    "winda", "taillift", "tail-lift", "tail lift", "tailift", "liftgate", "lift gate",
    "palletjack", "paleciak", "pallet jack", "hubwagen", "huckepack",
    "гидроборт", "подъемник", "подъёмник", "рокла", "рохля", "лифтборт",
]

# «Рефрижератор» на всех языках: заявки с упоминанием в ЛЮБОМ месте карточки исключаются
REEFER_KEYWORDS = [
    # Русский / украинский
    "рефрижератор",
    # Английский
    "reefer", "refrigerat", "fridge", "chiller", "frigorific",
    "temp controlled", "temperature control", "temp-controlled", "temperature-controlled",
    # Польский
    "chłodnia", "chłodnicz", "chlodnia", "chlodnicz", "lodówka", "lodowka",
    "mroźnia", "mroźn", "mroznia", "mrozn",
    # Немецкий
    "kühl", "kuehl", "kühlfahrzeug", "kuehlfahrzeug", "kühlauflieger", "kühlkoffer",
    "kühlzug", "kühlanhänger", "kühlaggregat", "thermo",
    # Итальянский / испанский / португальский / французский / румынский
    "frigo", "frigorifero", "frigorífico", "frigorifico", "frigorífica",
    "frigorifique", "frigider", "refrigerado", "refrigerato", "refrigere", "refrigerateur",
    # Чешский / словацкий
    "chladíren", "chladiren", "chladírensk", "chladirensk", "chladíc", "chladic",
    "chladíř", "mrazíren", "mraziren", "mrazíc", "mrazic",
    # Венгерский
    "hűtő", "hűtött", "hűtős", "hutokocsi", "hutogep", "hűtőkocsi", "fagyaszt",
    # Нидерландский
    "koel", "gekoeld", "diepvries",
    # Турецкий
    "frigorifik", "soğutucu", "sogutucu", "soğutmalı", "sogutmali",
    # Хорватский / сербский / боснийский
    "hladnjača", "hladnjaca", "rashladni", "frižider", "frizider",
    # Болгарский
    "хладилен",
    # Греческий
    "ψυγείο", "ψυκτικό",
    # Литовский / латышский
    "šaldytuv", "saldytuv", "refrižerator", "refrizerator", "saldetava",
    # Шведский / датский / норвежский
    "kylbil", "kyltransport", "kylaggregat", "kylvagn", "kyld", "frysbil",
    "køle", "kølevogn", "køletransport", "kjøle", "kjølevogn", "kjølebil",
    # Финский / эстонский
    "kylmä", "külmik", "kulmik", "külmutus", "kulmutus",
]

FORBIDDEN_KEYWORDS = FORBIDDEN_EQUIPMENT_KEYWORDS + REEFER_KEYWORDS


def _contains_forbidden_equipment(raw_data: Dict[str, Any]) -> bool:
    text = json.dumps(raw_data, ensure_ascii=False).lower()
    for kw in FORBIDDEN_KEYWORDS:
        if kw.lower() in text:
            return True
    return False


MAX_CARGO_LENGTH_CM = 480


def _contains_oversized_cargo(raw_data: Dict[str, Any]) -> bool:
    """Груз длиннее 480 см, если длина указана явно (например 600x50x50, 610x20x20, 500 cm)."""
    text = json.dumps(raw_data, ensure_ascii=False).lower()
    # тройки/пары размеров: 600x50x50, 200x80x250cm, 210 cm x 105 cm x 55 cm, 1x 600x40x30 cm
    for m in re.finditer(r'(?<![\d.,])(\d+(?:[.,]\d+)?)(?:\s*cm)?\s*[xх×]\s*(\d+(?:[.,]\d+)?)(?:\s*cm)?(?:\s*[xх×]\s*(\d+(?:[.,]\d+)?)(?:\s*cm)?)?', text):
        vals = []
        for g in (1, 2, 3):
            if m.group(g):
                vals.append(float(m.group(g).replace(',', '.')))
        if vals and max(vals) > MAX_CARGO_LENGTH_CM:
            return True
    # одиночная явная длина: 600 cm / 600cm
    for m in re.finditer(r'(?<![\d.,])(\d+(?:[.,]\d+)?)\s*cm\b', text):
        if float(m.group(1).replace(',', '.')) > MAX_CARGO_LENGTH_CM:
            return True
    return False


def _extract_country_code(place_raw: Optional[str]) -> Optional[str]:
    """AT 2432 Schwadorf -> AT"""
    if not place_raw:
        return None
    m = re.match(r'^([A-Za-z]{2})\s+\d', place_raw.strip())
    if m:
        return m.group(1).upper()
    m = re.match(r'^([A-Za-z]{2})\s*$', place_raw.strip())
    if m:
        return m.group(1).upper()
    return None


def map_to_cargo(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps raw extracted data to a normalized Cargo dict (DTO compatible).
    """
    
    if _contains_forbidden_equipment(raw_data):
        return None

    if _contains_oversized_cargo(raw_data):
        return None

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
            "country_code": _extract_country_code(raw_data.get("loading_place_raw")),
        },
        "unloading_place": {
            "raw": raw_data.get("unloading_place_raw"),
            "country_code": _extract_country_code(raw_data.get("unloading_place_raw")),
        },
        "offer_url": raw_data.get("offer_url"),
        "loading_date_raw": raw_data.get("loading_date_raw"),
        "unloading_date_raw": raw_data.get("unloading_date_raw"),
        "body_type": body_type,
        "weight": weight,
        "description": raw_data.get("description_raw"),
        "price": price,
        "currency": currency,
        "distance_trans_eu": distance_km,
        "company_name": raw_data.get("company_name"),
        "company_rating": raw_data.get("company_rating_raw"),
        "published_at": raw_data.get("published_at_raw"),
        "raw_data": raw_data # Keep raw validation
    }

def _parse_price(price_str: Optional[str]):
    if not price_str:
        return None, "EUR"
    
    # Remove whitespace
    clean = price_str.replace(" ", "").upper()
    
    # Extract number
    currency = "EUR"
    is_pln = False
    amount = 0.0
    
    if "PLN" in clean:
        is_pln = True
    
    # Simple regex for number
    match = re.search(r'[\d\.,]+', clean)
    if match:
        num_str = match.group(0).replace(",", ".")
        try:
            amount = float(num_str)
            # Conversion to EUR if PLN
            if is_pln:
                amount = round(amount / 4.3, 2)
        except ValueError:
            pass
            
    return amount, "EUR"

def _parse_distance(dist_str: Optional[str]) -> Optional[int]:
    if not dist_str:
        return None
    
    # "123 km"
    match = re.search(r'(\d+)', dist_str.replace(" ", ""))
    if match:
        return int(match.group(1))
    return None

def _parse_cargo_info(info_str: Optional[str]):
    # e.g. "0,1 т, цельномет, ящик, стандарт, штора"
    if not info_str:
        return None, None

    weight = None
    body = info_str

    # Извлекаем вес "0,1 т" / "24t" и убираем его из описания (типа кузова)
    w_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*т', info_str, re.IGNORECASE)
    if w_match:
        try:
            weight = float(w_match.group(1).replace(",", ".")) * 1000  # кг
        except Exception:
            pass
        body = (info_str[:w_match.start()] + info_str[w_match.end():]).strip(" ,")

    return body or None, weight
