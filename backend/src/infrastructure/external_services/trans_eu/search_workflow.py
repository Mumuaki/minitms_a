"""Pure, Playwright-free helpers for the Trans.eu search workflow.

These helpers implement the parsing, defaulting, validation and
dropdown-ranking rules from the Trans.eu search procedure
(``docs/Поиск_процедура.md``, ``automation_rules.md`` and ``spec_trans_eu.md``)
so they can be tested offline without a browser, database or network.

They have no side effects: no Playwright objects, no filesystem access, no
network access. ``client.py`` uses them as thin, trustable decision functions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta

_DATE_FORMAT = "%d.%m.%Y"

# ISO-2 country code: exactly two uppercase ASCII letters.
_ISO_RE = re.compile(r"^[A-Z]{2}$")

# Minimal Russian fallback map mirroring the existing client behaviour. Russian
# fallbacks are only attempted after the documented primary attempts fail to
# open a dropdown.
_RU_CITY_MAP = {
    "Berlin": "Берлин",
    "Warszawa": "Варшава",
    "Prague": "Прага",
    "Bratislava": "Братислава",
    "Dietfurt": "Дитфурт",
    "Šamorín": "Шаморин",
}


def parse_date_strict(value: str) -> date | None:
    """Parse a ``DD.MM.YYYY`` date strictly.

    ``None`` or blank input returns ``None`` (an automatic default is expected
    later). Any other non-empty, malformed or impossible value (for example
    ``"31.02.2026"``) raises ``ValueError`` so it can never be silently
    replaced with today or passed to the UI.
    """
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.strptime(text, _DATE_FORMAT)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid date {value!r}: expected DD.MM.YYYY"
        ) from exc
    # Enforce the zero-padded DD.MM.YYYY representation (round-trip check).
    if parsed.strftime(_DATE_FORMAT) != text:
        raise ValueError(
            f"Invalid date {value!r}: expected DD.MM.YYYY"
        )
    return parsed.date()


def validate_search_dates(
    date_from: str = None,
    date_to: str = None,
    unloading_date_from: str = None,
    unloading_date_to: str = None,
    *,
    today: date = None,
) -> tuple[str, str, str, str]:
    """Validate and default the four search dates.

    Blank/``None`` inputs keep the automatic defaults from the procedure:
    loading ``From`` = today, loading ``To`` = loading ``From``,
    unloading ``From`` = loading ``To`` + 1 day, unloading ``To`` = unloading
    ``From``. Explicit non-empty inputs are preserved exactly.

    Raises ``ValueError`` for malformed/impossible explicit inputs and for any
    chronology violation:

    * loading ``From`` is not in the past,
    * ``From`` <= ``To`` for loading and unloading,
    * both unloading bounds are >= the latest loading bound.

    Returns normalized ``(date_from, date_to, unloading_date_from,
    unloading_date_to)`` strings in ``DD.MM.YYYY`` format.
    """
    if today is None:
        today = date.today()

    df = parse_date_strict(date_from)
    dt = parse_date_strict(date_to)
    uf = parse_date_strict(unloading_date_from)
    ut = parse_date_strict(unloading_date_to)

    # Automatic defaults for blank/None inputs (explicit values preserved).
    if df is None:
        df = today
    if dt is None:
        dt = df
    if uf is None:
        uf = dt + timedelta(days=1)
    if ut is None:
        ut = uf

    if df < today:
        raise ValueError(
            f"Loading Date From {date_from} cannot be in the past."
        )
    if df > dt:
        raise ValueError(
            f"Loading Date: From ({date_from}) > To ({date_to})"
        )
    if uf > ut:
        raise ValueError(
            f"Unloading Date: From ({unloading_date_from}) > To ({unloading_date_to})"
        )

    latest_load = max(df, dt)
    if uf < latest_load:
        raise ValueError(
            "Unloading From must be >= the latest loading date bound."
        )
    if ut < latest_load:
        raise ValueError(
            "Unloading To must be >= the latest loading date bound."
        )

    return (
        df.strftime(_DATE_FORMAT),
        dt.strftime(_DATE_FORMAT),
        uf.strftime(_DATE_FORMAT),
        ut.strftime(_DATE_FORMAT),
    )


@dataclass(frozen=True)
class LocationQuery:
    """Parsed components of a location input string."""

    iso: str = ""
    postcode: str = ""
    city: str = ""
    city_ru: str = ""


def parse_location_input(value: str) -> LocationQuery:
    """Parse a location input string into country/postcode/city components.

    Supported representations:

    * ``{ISO}, {postcode}, {city-start}`` (for example ``IT, 00131, Ro``),
    * ``{ISO}, {postcode}`` (for example ``IT, 00131``),
    * ``{ISO}`` (for example ``IT``),
    * legacy city-only inputs (for example ``Warszawa`` or ``Berlin``).

    A second part that contains a digit is treated as a postcode; otherwise it
    is treated as a city name. The ISO code is recognised only when it is a
    two-letter uppercase token.
    """
    parts = [p.strip() for p in (value or "").split(",") if p.strip()]

    iso = ""
    postcode = ""
    city = ""

    if len(parts) == 1:
        if _ISO_RE.match(parts[0]):
            iso = parts[0]
        elif re.search(r"\d", parts[0]):
            postcode = parts[0]
        else:
            city = parts[0]
    elif len(parts) == 2:
        if _ISO_RE.match(parts[0]):
            iso = parts[0]
            second = parts[1]
            if re.search(r"\d", second):
                postcode = second
            else:
                city = second
        else:
            # Legacy "City, ISO" or "City, postcode" ordering.
            city = parts[0]
            if _ISO_RE.match(parts[1]):
                iso = parts[1]
            else:
                postcode = parts[1]
    elif len(parts) >= 3:
        iso, postcode, city = parts[0], parts[1], parts[2]

    return LocationQuery(
        iso=iso,
        postcode=postcode,
        city=city,
        city_ru=_RU_CITY_MAP.get(city, city),
    )


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = item[0]
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def build_location_attempts(query: LocationQuery) -> list[tuple[str, str]]:
    """Build the ordered list of input attempts for a location query.

    Documented order for constrained inputs (ISO and/or postcode present):

    1. ``{ISO}, {postcode}, {city}``
    2. ``{ISO}, {postcode}``
    3. ``{ISO}``

    followed by the permitted Russian fallbacks (city RU, then ISO + city RU),
    which the caller only reaches when the primary attempts produce no
    dropdown. Legacy city-only callers keep their conservative behaviour:
    city text first, then the Russian translation.

    Returns ``(attempt_text, city_for_ranking)`` tuples. ``city_for_ranking``
    is the city token used when scoring dropdown candidates. The ORIGINAL
    city signal is kept for every primary attempt (the typed text becomes
    broader, but the user's city intent must not be lost); the translated
    (Russian) signal is used only for the Russian fallback attempts.
    """
    attempts = []

    if query.iso or query.postcode:
        if query.iso and query.postcode and query.city:
            attempts.append((f"{query.iso}, {query.postcode}, {query.city}", query.city))
        if query.iso and query.postcode:
            attempts.append((f"{query.iso}, {query.postcode}", query.city))
        # «ISO, город» (без индекса) — тоже валидный ввод: печатать его целиком,
        # иначе город теряется и выбирается произвольная точка по одной стране.
        if query.iso and query.city and not query.postcode:
            attempts.append((f"{query.iso}, {query.city}", query.city))
        if query.iso:
            attempts.append((query.iso, query.city))
        elif query.postcode:
            attempts.append((query.postcode, query.city))

        if query.city_ru:
            attempts.append((query.city_ru, query.city_ru))
            if query.iso:
                attempts.append((f"{query.iso}, {query.city_ru}", query.city_ru))
    else:
        # Legacy city-only callers: conservative order, explicit text first.
        if query.city:
            attempts.append((query.city, query.city))
        if query.city_ru and query.city_ru != query.city:
            attempts.append((query.city_ru, query.city_ru))

    return _dedupe(attempts)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9]+", text.upper()))


_CITY_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


def _postcode_regex(postcode: str) -> re.Pattern | None:
    """Build a boundary-aware regex for an exact postal identifier.

    Separator runs inside the postcode (``-``, space, …) may be written with
    a non-word separator run in the candidate text, so ``00-001`` matches
    ``00 001``. Unicode word boundaries make the identifier a complete token:
    ``00131`` never matches ``001310``, ``100131`` or an accented word such as
    ``é00131``, and it can never combine unrelated neighbouring digits.
    Returns ``None`` when ``postcode`` is empty (no constraint) or when it has
    no alphanumeric characters; a non-empty postcode made entirely of
    separators/punctuation is malformed and must be rejected by the caller.
    """
    pc = (postcode or "").strip().upper()
    if not pc:
        return None
    chunks = [re.escape(chunk) for chunk in re.split(r"[^A-Za-z0-9]+", pc) if chunk]
    if not chunks:
        return None
    body = r"[^\w]+".join(chunks)
    return re.compile(r"(?<!\w)" + body + r"(?!\w)", re.IGNORECASE)


def _city_matches(text: str, city: str) -> bool:
    """Return True when ``text`` contains ``city`` as a case-insensitive,
    Unicode-aware START/TOKEN prefix, including multiword city phrases.

    Every query word must match consecutively starting at a token boundary.
    All but the final query word must match a whole word, while the final word
    may be a partial prefix (``Ro`` matches ``Roma``, ``New Yo`` matches
    ``New York``). A multiword query never matches only one of its components
    (``New York`` does not match ``York`` or ``Newcastle``), and an interior
    substring never counts (``Ro`` does not match ``Grosseto``).
    """
    city = (city or "").strip().casefold()
    if not city:
        return False
    words = [re.escape(w) for w in _CITY_WORD_RE.findall(city)]
    if not words:
        return False
    folded = (text or "").casefold()
    if len(words) == 1:
        pattern = r"(?<!\w)" + words[0]
    else:
        pattern = r"(?<!\w)" + words[0]
        for w in words[1:-1]:
            pattern += r"[^\w]+" + w
        pattern += r"[^\w]+" + words[-1]
    return re.search(pattern, folded) is not None


def rank_location_options(
    option_texts: list[str],
    *,
    iso: str = "",
    postcode: str = "",
    city: str = "",
) -> int | None:
    """Pick the best dropdown candidate index, or ``None`` if none qualify.

    Representation assumptions for ``option_texts`` (documented here so the
    ranking is auditable without a live portal): an option is a single string
    whose tokens include the country ISO-2 code (two uppercase letters) and/or
    the postal code (digits, possibly hyphen/space separated) and the
    city/region name. Matching is case-insensitive. The ISO code is matched as
    a whitespace-separated token; the postcode is matched as an exact,
    boundary-aware identifier with separator equivalence (so ``00-001``
    matches ``00 001`` but never a longer identifier); the city is matched as
    a case-insensitive START/TOKEN prefix, including multiword phrase prefixes
    (the procedure allows entering only the start of the city name).

    Rules:

    * A candidate that does not contain the requested ISO code (when one is
      requested) is rejected — a different country is never selected.
    * A candidate that does not contain the requested postcode (when one is
      requested) is rejected — a different postcode is never selected.
    * When the city is the ONLY available criterion, a candidate with no city
      match is rejected — an unrelated city is never selected.
    * When an ISO/postcode constraint is present, the city is a soft
      preference: among candidates matching the explicit ISO/postcode, one
      that also starts with the requested city prefix wins; the longest text
      is only a tiebreaker. When no candidate matches the city, the documented
      maximum-character-match policy applies among the ISO/postcode-compatible
      candidates (this is NOT an exact city filter).
    """
    iso = (iso or "").strip().upper()
    postcode = (postcode or "").strip().upper()
    city = (city or "").strip()

    postcode_re = _postcode_regex(postcode)
    if postcode and postcode_re is None:
        raise ValueError(
            f"Malformed postal identifier: {postcode!r} contains no alphanumeric characters"
        )
    city_required = bool(city) and not iso and not postcode

    best_index = None
    best_score = -1
    best_len = -1

    for idx, raw in enumerate(option_texts):
        text = (raw or "").strip()
        upper = text.upper()
        tokens = _tokens(upper)

        if iso and iso not in tokens:
            continue
        if postcode_re and not postcode_re.search(text):
            continue
        city_matches = _city_matches(text, city) if city else False
        if city_required and not city_matches:
            continue

        score = 0
        if iso:
            score += 1
        if postcode_re:
            score += 1
        if city and city_matches:
            score += 1

        if score > best_score or (score == best_score and len(text) > best_len):
            best_score = score
            best_len = len(text)
            best_index = idx

    return best_index


_MONTHS = {
    "январь": 1,
    "января": 1,
    "февраль": 2,
    "февраля": 2,
    "март": 3,
    "марта": 3,
    "апрель": 4,
    "апреля": 4,
    "май": 5,
    "мая": 5,
    "июнь": 6,
    "июня": 6,
    "июль": 7,
    "июля": 7,
    "август": 8,
    "августа": 8,
    "сентябрь": 9,
    "сентября": 9,
    "октябрь": 10,
    "октября": 10,
    "ноябрь": 11,
    "ноября": 11,
    "декабрь": 12,
    "декабря": 12,
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def parse_calendar_header(header_text: str) -> tuple[int, int] | None:
    """Parse a calendar header like ``"октябрь 2026"`` into ``(month, year)``.

    Tolerates the real portal's formatting quirks: non-breaking or narrow
    spaces, a trailing ``г.`` and the genitive month form (``октября``).
    Returns ``None`` when the header cannot be parsed unambiguously.
    """
    text = (header_text or "").lower().strip()
    # Normalize every unicode space variant to a plain ASCII space.
    text = re.sub(r"[\s\u00a0\u2007\u202f]+", " ", text)
    text = text.replace(" г.", " ").replace(" г ", " ").rstrip(" .")
    parts = text.split()
    if len(parts) < 2:
        return None
    month = _MONTHS.get(parts[0])
    year_str = parts[-1]
    if month is None or not year_str.isdigit():
        return None
    return month, int(year_str)


# Strict inclusive maxima for the Trans.eu portal search (portal units):
# weight in tonnes, length in metres. These are mandatory upper bounds, not
# merely default values; wider requests are rejected rather than silently run.
MAX_WEIGHT_TONNES = "0.9"
MAX_LENGTH_METRES = "4.8"


def _positive_decimal(value, label: str) -> "Decimal | None":
    from decimal import Decimal, InvalidOperation

    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite positive number")
    try:
        if isinstance(value, Decimal):
            number = value
        elif isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            # Accept the European decimal comma ("4,8") as well as the dot.
            number = Decimal(stripped.replace(",", "."))
        else:
            number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} must be a finite positive number")
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{label} must be a finite positive number")
    return number


def _format_decimal(number: "Decimal") -> str:
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def resolve_trans_eu_limits(
    weight_to: str = None,
    length_to: str = None,
) -> tuple[str, str]:
    """Return the validated portal ``(weight_to, length_to)`` strings.

    Blank/``None`` inputs keep the authoritative defaults ``0.9`` (t) and
    ``4.8`` (m). Explicit values must be finite positive numbers; a value above
    the strict maximum is rejected with ``ValueError`` so an oversize request
    is never silently shown. Returns normalised numeric strings (``"0.9"``,
    ``"4.8"``).
    """
    from decimal import Decimal

    weight = _positive_decimal(weight_to, "weight_to") if weight_to not in (None, "") else None
    if weight is None:
        weight = Decimal(MAX_WEIGHT_TONNES)
    if weight > Decimal(MAX_WEIGHT_TONNES):
        raise ValueError(
            f"weight_to {_format_decimal(weight)} t exceeds the strict maximum {MAX_WEIGHT_TONNES} t"
        )

    length = _positive_decimal(length_to, "length_to") if length_to not in (None, "") else None
    if length is None:
        length = Decimal(MAX_LENGTH_METRES)
    if length > Decimal(MAX_LENGTH_METRES):
        raise ValueError(
            f"length_to {_format_decimal(length)} m exceeds the strict maximum {MAX_LENGTH_METRES} m"
        )

    return _format_decimal(weight), _format_decimal(length)
