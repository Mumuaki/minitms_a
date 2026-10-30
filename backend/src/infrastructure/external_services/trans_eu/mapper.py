"""
Mapper module for Trans.eu offers.
Converts raw dictionary data from parser into normalized domain structures.
"""
from typing import Dict, Any, Optional
import re
from datetime import datetime

from backend.src.domain.value_objects.body_type import normalize_body_type
from backend.src.domain.value_objects.trans_eu_filter import is_excluded_trans_eu_body


# A numeric token: a plain decimal ("900", "0.9", "850,5") or a thousands-
# grouped decimal ("1 000", "1\u00a0000", "1 234,5"). Group separators are
# space, NBSP and thin space and must separate 3-digit groups.
_NUMBER_TOKEN = r'(\d{1,3}(?:[\s\u00a0\u202f]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)'

# Weight in tons ("24t", "24 t", "0.15 т"). The unit must be followed by a
# word boundary so "24Tent" is never parsed as "24t".
_WEIGHT_TON_RE = re.compile(
    rf'(?<![\d.,\-\u2212\u2013\u2014]){_NUMBER_TOKEN}(?![\d])\s*[tт](?![\w])',
    re.IGNORECASE,
)

# Weight in kilograms ("900 kg", "850 kg", "850кг"). Both the Latin "kg" and
# the Cyrillic "кг" units are accepted; an absent/unparseable unit never
# becomes an invented zero.
_WEIGHT_KG_RE = re.compile(
    rf'(?<![\d.,\-\u2212\u2013\u2014]){_NUMBER_TOKEN}(?![\d])\s*(?:kg|кг)(?![\w])',
    re.IGNORECASE,
)

# Length in loading metres / LDM ("4.8 ldm", "13,6 LDM", "4.8 погр. м").
# Only unambiguous length units are accepted; a bare "м" is avoided because it
# is ambiguous with cubic metres / seats etc.
_LENGTH_RE = re.compile(
    r'(?<![\d.,\-\u2212\u2013\u2014])(\d+(?:[.,]\d+)?)\s*(?:ldm|погр\.?\s*м|погрузочн\w*\s*м|loading\s+meters?|load\s+meters?)',
    re.IGNORECASE,
)


_NEG_SIGNS = '-\u2212\u2013\u2014'


def _has_invalid_lead(text: str, match_start: int) -> bool:
    """Return True when a numeric match has a forbidden leading context.

    A number must not be led (directly or through whitespace) by a sign/range
    dash or by another numeric fragment, which would mark it as a negative
    quantity, a range boundary or a malformed grouped value.
    """
    j = match_start - 1
    while j >= 0 and text[j].isspace():
        j -= 1
    if j < 0:
        return False
    ch = text[j]
    return ch.isdigit() or ch in _NEG_SIGNS


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
        "length_m": _parse_length_ldm(raw_data.get("cargo_info_raw", "")),
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


def _number_to_float(number_str: str) -> Optional[float]:
    """Convert a matched numeric token to ``float`` or ``None`` on failure.

    Thousands-grouped tokens (space/NBSP/thin-space separated) have their
    separators removed and a comma is treated as the decimal point.
    """
    if not number_str:
        return None
    cleaned = re.sub(r'[\s\u00a0\u202f]', '', number_str).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_cargo_info(info_str: Optional[str]):
    # e.g. "24t, Curtain, 13.6 ldm"
    if info_str is None or not info_str.strip():
        return None, None

    # Check raw forbidden-body tokens (e.g. "Ref") BEFORE normalizing: the
    # normalizer can collapse "Tent, Ref" to canonical "Tent" and silently drop
    # the excluded token. When the raw body is forbidden it is preserved
    # verbatim so the shared admission policy rejects it downstream.
    if is_excluded_trans_eu_body(info_str):
        body = info_str
    else:
        body = normalize_body_type(info_str)
        if body is None:
            body = info_str

    # Extract weight: tonnes are converted to kg; explicit kg values are used
    # as-is. Missing/unknown, negative, ranged, grouped-fragment or multiple
    # weights never become an invented zero: they stay ``None`` (unknown).
    weight = None
    kg_matches = [
        m for m in _WEIGHT_KG_RE.finditer(info_str)
        if not _has_invalid_lead(info_str, m.start())
    ]
    ton_matches = [
        m for m in _WEIGHT_TON_RE.finditer(info_str)
        if not _has_invalid_lead(info_str, m.start())
    ]
    if len(kg_matches) + len(ton_matches) == 1:
        if kg_matches:
            weight = _number_to_float(kg_matches[0].group(1))
        else:
            tons = _number_to_float(ton_matches[0].group(1))
            weight = None if tons is None else tons * 1000

    return body, weight


def _parse_length_ldm(info_str: Optional[str]) -> Optional[float]:
    """Parse a length/LDM value in metres, or ``None`` when it is unknown.

    Accepts ``"4.8 ldm"``, ``"13,6 LDM"`` and ``"4.8 м"``. The value is never
    rounded, clamped or defaulted to zero; an absent/unparseable length stays
    ``None`` so callers treat it as unknown rather than as verified.
    """
    if info_str is None or not info_str.strip():
        return None
    matches = [
        m for m in _LENGTH_RE.finditer(info_str)
        if not _has_invalid_lead(info_str, m.start())
    ]
    if len(matches) != 1:
        return None
    try:
        return float(matches[0].group(1).replace(",", "."))
    except ValueError:
        return None
