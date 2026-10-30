"""Offline tests for the Trans.eu search procedure conformance (package 16).

These tests mock Playwright and login: no browser, no database and no network
are used. They exercise the pure ``search_workflow`` helpers directly and the
``TransEuClient`` preparation / location / calendar methods through a tiny fake
Playwright page, so the procedure rules are checked as behaviour rather than
mirrored implementation.

Plain ``asyncio.run`` is used instead of pytest-asyncio so the tests do not
depend on a specific async plugin.
"""

import asyncio
from datetime import date, timedelta

import pytest

from backend.src.infrastructure.external_services.trans_eu import search_workflow
from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient


MODAL_SELECTOR = 'div[role="option"]'
# Живой портал: контейнера `advanced-filters` (через дефис) нет; признак
# раскрытой расширенной панели — поле даты, которое проверяется по кликабельности.
ADVANCED_SELECTOR = 'div[data-ctx="dateinput-field"]'
DATE_INPUT_SELECTOR = 'div[data-ctx="dateinput-field"] input[name="from"]'
LOADING_SELECTOR = 'div[data-ctx="place-loading_place-0"] input'
MORE_SELECTOR = 'button:has-text("MORE FILTERS")'
# Живой портал: «Очистить фильтры» — ссылка <a data-ctx="basic-filters-form-clear-filters">.
CLEAR_SELECTOR = '[data-ctx="basic-filters-form-clear-filters"]'
SUBMIT_SELECTOR = 'button[data-ctx="basicFilters.form.submit"]'


# ---------------------------------------------------------------------------
# Fake Playwright page / locator
# ---------------------------------------------------------------------------
class FakeLocator:
    def __init__(self, page, selector, index=None):
        self.page = page
        self.selector = selector
        self.index = index

    def _combine(self, sub):
        return f"{self.selector} {sub}".strip()

    def locator(self, sub):
        return FakeLocator(self.page, self._combine(sub), None)

    @property
    def first(self):
        return FakeLocator(self.page, self.selector, 0)

    def nth(self, i):
        return FakeLocator(self.page, self.selector, i)

    async def count(self):
        node = self.page.nodes.get(self.selector)
        if node is None:
            return 0
        if "texts" in node:
            return len(node["texts"])
        return node.get("count", 1)

    async def is_visible(self, timeout=None):
        node = self.page.nodes.get(self.selector)
        return node is not None and node.get("visible", True)

    async def wait_for(self, state=None, timeout=None):
        node = self.page.nodes.get(self.selector)
        if node is None or not node.get("visible", True):
            raise TimeoutError(f"{self.selector} not {state}")
        return None

    async def click(self, force=False):
        self.page.clicked.append((self.selector, self.index))
        node = self.page.nodes.get(self.selector)
        if node is not None:
            if "raise_on_click" in node:
                raise node["raise_on_click"]
            effect = node.get("click_effect")
            if effect:
                for sel, value in effect.items():
                    self.page.nodes.setdefault(sel, {})["visible"] = value

    async def text_content(self):
        node = self.page.nodes.get(self.selector)
        if node is None:
            return ""
        texts = node.get("texts")
        if texts is not None:
            if self.index is not None:
                return texts[self.index % len(texts)]
            cursor = node.get("_cursor", 0)
            node["_cursor"] = (cursor + 1) % len(texts)
            return texts[cursor]
        return node.get("text", "")

    async def all(self):
        node = self.page.nodes.get(self.selector)
        if node is None:
            return []
        if "texts" in node:
            size = len(node["texts"])
        else:
            size = node.get("count", 0)
        return [FakeLocator(self.page, self.selector, i) for i in range(size)]

    async def scroll_into_view_if_needed(self):
        return None

    async def evaluate(self, js):
        return None

    async def focus(self):
        self.page.clicked.append((f"{self.selector} [focus]", self.index))
        return None

    async def fill(self, value):
        self.page.filled.append((self.selector, value))
        return None

    async def press(self, key):
        self.page.pressed.append((self.selector, key))
        return None


class FakeKeyboard:
    def __init__(self, page):
        self.page = page

    async def press(self, key):
        self.page.pressed.append(key)

    async def type(self, text, delay=0):
        self.page.typed.append(text)


class FakePage:
    def __init__(self, nodes=None, *, modal_selector=None, modal_visible=None):
        self.nodes = dict(nodes or {})
        self.modal_selector = modal_selector
        self.modal_visible = modal_visible or (lambda typed: True)
        self.clicked = []
        self.typed = []
        self.pressed = []
        self.filled = []
        self.goto_calls = []
        self.screenshots = []

    def locator(self, selector):
        return FakeLocator(self, selector)

    async def wait_for_selector(self, selector, state=None, timeout=None):
        if selector == self.modal_selector:
            if self.modal_visible(self.typed):
                return None
            raise TimeoutError(f"{selector} not visible")
        node = self.nodes.get(selector)
        if node is None or not node.get("visible", True):
            raise TimeoutError(f"{selector} not {state}")
        return None

    async def wait_for_timeout(self, ms):
        return None

    async def goto(self, url, timeout=None, wait_until=None):
        self.goto_calls.append(url)
        return None

    async def screenshot(self, path=None):
        self.screenshots.append(path)
        return None

    async def content(self):
        return ""

    async def evaluate(self, js, arg=None):
        if arg is not None:
            # _is_clickable: элемент «кликабелен», если он есть в nodes и visible.
            node = self.nodes.get(arg)
            return bool(node and node.get("visible", False))
        return []

    @property
    def keyboard(self):
        return FakeKeyboard(self)


def _client(page=None):
    client = TransEuClient()
    client.page = page
    client.login_calls = 0
    client.location_calls = []

    async def login():
        client.login_calls += 1
        return True

    async def cloudflare():
        return False

    async def location_stub(container_selector, value, radius=0):
        client.location_calls.append((container_selector, value, radius))

    client.login = login
    client._wait_for_cloudflare_if_present = cloudflare
    client._set_location_field = location_stub
    return client


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Pure date helpers
# ---------------------------------------------------------------------------
def test_parse_date_strict_rejects_malformed_and_impossible():
    for bad in ["31.02.2026", "2026-02-15", "15/02/2026", "1.2.2026", "15.13.2026", "garbage"]:
        with pytest.raises(ValueError):
            search_workflow.parse_date_strict(bad)


def test_parse_date_strict_accepts_valid_and_blank():
    assert search_workflow.parse_date_strict(None) is None
    assert search_workflow.parse_date_strict("") is None
    assert search_workflow.parse_date_strict("   ") is None
    assert search_workflow.parse_date_strict("15.02.2026") == date(2026, 2, 15)


def test_validate_search_dates_applies_automatic_defaults():
    today = date(2026, 10, 3)
    df, dt, uf, ut = search_workflow.validate_search_dates(today=today)
    assert df == "03.10.2026"
    assert dt == "03.10.2026"
    assert uf == "04.10.2026"
    assert ut == "04.10.2026"


def test_validate_search_dates_preserves_explicit_values():
    today = date(2026, 10, 3)
    df, dt, uf, ut = search_workflow.validate_search_dates(
        date_from="05.10.2026",
        date_to="06.10.2026",
        unloading_date_from="07.10.2026",
        unloading_date_to="08.10.2026",
        today=today,
    )
    assert (df, dt, uf, ut) == ("05.10.2026", "06.10.2026", "07.10.2026", "08.10.2026")


def test_validate_search_dates_rejects_range_and_chronology_violations():
    today = date(2026, 10, 3)

    with pytest.raises(ValueError):
        # loading From > loading To
        search_workflow.validate_search_dates(
            date_from="08.10.2026", date_to="06.10.2026", today=today
        )

    with pytest.raises(ValueError):
        # unloading From > unloading To
        search_workflow.validate_search_dates(
            date_from="05.10.2026",
            date_to="05.10.2026",
            unloading_date_from="08.10.2026",
            unloading_date_to="07.10.2026",
            today=today,
        )

    with pytest.raises(ValueError):
        # unloading bound earlier than the latest loading bound
        search_workflow.validate_search_dates(
            date_from="05.10.2026",
            date_to="08.10.2026",
            unloading_date_from="07.10.2026",
            unloading_date_to="09.10.2026",
            today=today,
        )

    with pytest.raises(ValueError):
        # loading From in the past
        search_workflow.validate_search_dates(date_from="01.10.2026", today=today)


def test_validate_search_dates_defaults_unload_from_loading_to_plus_one():
    today = date(2026, 10, 3)
    df, dt, uf, ut = search_workflow.validate_search_dates(
        date_from="05.10.2026", date_to="06.10.2026", today=today
    )
    assert (df, dt, uf, ut) == ("05.10.2026", "06.10.2026", "07.10.2026", "07.10.2026")


# ---------------------------------------------------------------------------
# Pure location parsing / ranking helpers
# ---------------------------------------------------------------------------
def test_parse_location_input_formats():
    q = search_workflow.parse_location_input("IT, 00131, Ro")
    assert (q.iso, q.postcode, q.city) == ("IT", "00131", "Ro")

    q = search_workflow.parse_location_input("DE, 80301")
    assert (q.iso, q.postcode, q.city) == ("DE", "80301", "")

    q = search_workflow.parse_location_input("IT")
    assert (q.iso, q.postcode, q.city) == ("IT", "", "")

    q = search_workflow.parse_location_input("Warszawa")
    assert (q.iso, q.postcode, q.city, q.city_ru) == ("", "", "Warszawa", "Варшава")


def test_build_location_attempts_documented_order():
    q = search_workflow.parse_location_input("PL, 00-001, Warszawa")
    attempts = [text for text, _ in search_workflow.build_location_attempts(q)]
    assert attempts == ["PL, 00-001, Warszawa", "PL, 00-001", "PL", "Варшава", "PL, Варшава"]


def test_build_location_attempts_legacy_city_only_conservative():
    q = search_workflow.parse_location_input("Warszawa")
    attempts = [text for text, _ in search_workflow.build_location_attempts(q)]
    assert attempts == ["Warszawa", "Варшава"]


def test_build_location_attempts_keeps_explicit_ru_city_constraint():
    q = search_workflow.parse_location_input("PL, Варшава")
    attempts = [text for text, _ in search_workflow.build_location_attempts(q)]
    assert attempts == ["PL, Варшава", "PL", "Варшава"]


def test_build_location_attempts_keeps_latin_city_with_iso():
    # «ISO, город» (без индекса) не должен терять город: первый ввод — целиком.
    q = search_workflow.parse_location_input("SK, Bratislava")
    attempts = [text for text, _ in search_workflow.build_location_attempts(q)]
    assert attempts[0] == "SK, Bratislava"
    assert attempts == ["SK, Bratislava", "SK", "Братислава", "SK, Братислава"]


def test_build_location_attempts_retains_original_city_signal_on_primary_attempts():
    q = search_workflow.parse_location_input("IT, 00131, Ro")
    attempts = search_workflow.build_location_attempts(q)
    # Text order stays documented; the original city signal is never dropped
    # when the primary attempt becomes broader (ISO+postcode / ISO).
    assert attempts[0] == ("IT, 00131, Ro", "Ro")
    assert attempts[1] == ("IT, 00131", "Ro")
    assert attempts[2] == ("IT", "Ro")


def test_rank_location_options_rejects_wrong_postcode_longer_option():
    texts = [
        "Milan, 20121, IT, Lombardy, Italy, Europe, deliberately longest but wrong postcode",
        "Roma 00131, IT",
        "Roma 00131, IT, Lazio, Rome metropolitan area, most complete compatible record",
    ]
    best = search_workflow.rank_location_options(texts, iso="IT", postcode="00131", city="Ro")
    assert best == 2


def test_rank_location_options_iso_only_uses_longest_tiebreaker():
    texts = ["IT", "Roma 00131, IT, Lazio"]
    best = search_workflow.rank_location_options(texts, iso="IT")
    assert best == 1


def test_rank_location_options_returns_none_when_none_compatible():
    texts = ["Berlin 10115, DE", "Prague 11000, CZ"]
    assert search_workflow.rank_location_options(texts, iso="IT", postcode="00131") is None


def test_rank_location_options_postcode_is_exact_not_substring():
    texts = [
        "Milano 001310, IT, Lombardy, longer wrong superset postcode",
        "Roma 100131, IT, longer wrong postcode with leading digit",
        "Roma 00131, IT, Lazio, correct",
    ]
    best = search_workflow.rank_location_options(texts, iso="IT", postcode="00131")
    assert best == 2


def test_rank_location_options_postcode_separator_equivalence():
    # "00-001" must match "00-001" and "00 001" but never a longer identifier.
    hyphenated = [
        "Warszawa 00-0010, PL, longer wrong postcode",
        "Warszawa 00-001, PL, Mazowieckie",
    ]
    assert search_workflow.rank_location_options(hyphenated, iso="PL", postcode="00-001") == 1

    spaced = ["Warszawa 00 001, PL, Mazowieckie"]
    assert search_workflow.rank_location_options(spaced, iso="PL", postcode="00-001") == 0
    assert search_workflow.rank_location_options(spaced, iso="PL", postcode="00 001") == 0


def test_rank_location_options_postcode_alphanumeric_boundary():
    texts = [
        "London SW1A 1AAB, GB, longer wrong alphanumeric postcode",
        "London SW1A 1AA, GB, Westminster",
    ]
    best = search_workflow.rank_location_options(texts, iso="GB", postcode="SW1A 1AA")
    assert best == 1


def test_rank_location_options_postcode_rejects_malformed_identifiers():
    texts = ["Roma 00131, IT, Lazio"]
    with pytest.raises(ValueError):
        search_workflow.rank_location_options(texts, postcode="---")
    with pytest.raises(ValueError):
        search_workflow.rank_location_options(texts, postcode=".,-")
    # A blank postcode means "no constraint", not a malformed identifier.
    assert search_workflow.rank_location_options(texts, postcode="") == 0


def test_rank_location_options_postcode_requires_real_separator():
    # A compacted digit run is a different identifier, not an equivalent
    # spelling of the separated postcode.
    texts = [
        "Warszawa 00001, PL",
        "Warszawa 00-001, PL, Mazowieckie",
    ]
    assert search_workflow.rank_location_options(texts, iso="PL", postcode="00-001") == 1


def test_rank_location_options_postcode_unicode_word_boundary():
    # A postcode glued to an accented letter is part of a word, not a token.
    texts = [
        "Pré00131, IT",
        "Roma 00131, IT, Lazio",
    ]
    assert search_workflow.rank_location_options(texts, iso="IT", postcode="00131") == 1


def test_rank_location_options_city_only_rejects_unrelated_city():
    texts = [
        "Berlin 10115, DE, Germany, Brandenburg, Europa, deliberately long unrelated",
        "Prague 110 00, CZ, Czech Republic, Praha",
    ]
    assert search_workflow.rank_location_options(texts, city="Warszawa") is None


def test_rank_location_options_city_prefix_beats_interior_substring():
    # "Ro" is a START/TOKEN prefix: it matches Roma, never Grosseto (interior).
    texts = [
        "Grosseto 58100, IT, Tuscany, Maremma coastal town",
        "Roma 00131, IT, Lazio",
    ]
    # The interior "ro" in Grosseto alone must not match the "Ro" prefix.
    assert search_workflow.rank_location_options(texts[:1], city="Ro") is None
    assert search_workflow.rank_location_options(texts, city="Ro") == 1


def test_rank_location_options_prefers_city_match_over_length():
    # With explicit ISO+postcode, the requested city prefix wins over a longer
    # same-postcode candidate that has no city match.
    texts = [
        "Bergamo 00131, IT, Lombardy, very long unrelated city",
        "Roma 00131, IT, Lazio",
    ]
    assert search_workflow.rank_location_options(texts, iso="IT", postcode="00131", city="Ro") == 1


def test_rank_location_options_city_multiword_phrase_and_partial_prefix():
    # "New York" and its partial prefix "New Yo" match the full phrase;
    # "York" alone, "Newcastle" and "New Jersey" do not.
    texts = [
        "York, NY, US",
        "Newcastle, GB, UK",
        "New Jersey, NJ, US",
        "New York, NY, US",
        "Manhattan, New York, NY, US",
    ]
    assert search_workflow.rank_location_options(texts, city="New York") == 4
    assert search_workflow.rank_location_options(texts, city="New Yo") == 4


def test_rank_location_options_city_multiword_rejects_components_and_interior():
    # "New York" is one phrase: neither "York" alone nor "Newcastle" (single
    # token) nor "newyork" (compacted token) qualifies.
    texts = [
        "York, NY, US",
        "Newcastle, GB, UK",
        "Newyork, NY, US",
        "New York, NY, US",
    ]
    assert search_workflow.rank_location_options(texts, city="New York") == 3


def test_rank_location_options_city_multiword_unicode():
    # Unicode case-insensitive multiword phrase: full and partial prefix match;
    # the trailing component alone ("Paulo") never satisfies "São Paulo".
    texts = [
        "Paulo, BR",
        "Santos, SP, BR",
        "Rio de Janeiro, RJ, BR",
        "São Paulo, SP, BR",
    ]
    assert search_workflow.rank_location_options(texts, city="São Paulo") == 3
    assert search_workflow.rank_location_options(texts, city="São Pa") == 3


def test_parse_calendar_header():
    assert search_workflow.parse_calendar_header("январь 2026") == (1, 2026)
    assert search_workflow.parse_calendar_header("February 2026") == (2, 2026)
    assert search_workflow.parse_calendar_header("not a header") is None


# ---------------------------------------------------------------------------
# search_offers: strict dates fail before login / UI
# ---------------------------------------------------------------------------
def test_search_offers_malformed_date_fails_before_login():
    client = _client(page=None)
    with pytest.raises(ValueError):
        _run(client.search_offers(
            loading_location="IT, 00131",
            unloading_location="",
            date_from="31.02.2026",
        ))
    assert client.login_calls == 0


def test_search_offers_range_violation_fails_before_login():
    client = _client(page=None)
    today = date.today()
    with pytest.raises(ValueError):
        _run(client.search_offers(
            loading_location="IT, 00131",
            unloading_location="",
            date_from=(today + timedelta(days=5)).strftime("%d.%m.%Y"),
            date_to=(today + timedelta(days=2)).strftime("%d.%m.%Y"),
        ))
    assert client.login_calls == 0


# ---------------------------------------------------------------------------
# Filter preparation
# ---------------------------------------------------------------------------
def test_prepare_filters_clicks_more_when_base_already_visible():
    page = FakePage(nodes={
        LOADING_SELECTOR: {"visible": True},
        DATE_INPUT_SELECTOR: {"visible": False},
        MORE_SELECTOR: {
            "visible": True,
            "click_effect": {DATE_INPUT_SELECTOR: True},
        },
        CLEAR_SELECTOR: {"visible": True},
    })
    client = _client(page=page)

    _run(client._prepare_filters())

    assert (MORE_SELECTOR, 0) in page.clicked
    assert (CLEAR_SELECTOR, 0) in page.clicked
    assert page.nodes[DATE_INPUT_SELECTOR]["visible"] is True


def test_prepare_filters_does_not_click_more_when_advanced_already_open():
    page = FakePage(nodes={
        LOADING_SELECTOR: {"visible": True},
        DATE_INPUT_SELECTOR: {"visible": True},
        MORE_SELECTOR: {"visible": True},
        CLEAR_SELECTOR: {"visible": True},
    })
    client = _client(page=page)

    _run(client._prepare_filters())

    assert not any(sel == MORE_SELECTOR for sel, _ in page.clicked)
    assert (CLEAR_SELECTOR, 0) in page.clicked


def test_prepare_filters_raises_when_advanced_panel_missing():
    page = FakePage(nodes={
        LOADING_SELECTOR: {"visible": True},
        DATE_INPUT_SELECTOR: {"visible": False},
    })
    client = _client(page=page)

    with pytest.raises(Exception, match="Advanced filters panel"):
        _run(client._prepare_filters())


def test_prepare_filters_clears_chips_when_no_clear_all_button():
    # На текущем портале нет единой кнопки «Очистить фильтры»: сброс выполняется
    # закрытием чипов предпросмотра (button[data-ctx="close"]). Скрипт должен
    # очистить чипы, а не отказываться от поиска.
    page = FakePage(nodes={
        LOADING_SELECTOR: {"visible": True},
        DATE_INPUT_SELECTOR: {"visible": True},
        '[data-ctx="filter-preview"] button[data-ctx="close"]': {"visible": True},
    })
    client = _client(page=page)

    _run(client._prepare_filters())

    close_sel = '[data-ctx="filter-preview"] button[data-ctx="close"]'
    assert any(sel == close_sel for sel, _ in page.clicked)


def test_search_offers_proceeds_when_clear_missing_and_filters_clean():
    # No clear control AND no active filter chips: nothing to clear, so the
    # search must proceed instead of failing on a hidden clear button.
    page = FakePage(nodes={
        SUBMIT_SELECTOR: {"visible": True},
        LOADING_SELECTOR: {"visible": True},
        DATE_INPUT_SELECTOR: {"visible": True},
        # clear button and filter chips intentionally absent
    })
    client = _client(page=page)

    _run(client.search_offers(
        loading_location="IT, 00131",
        unloading_location="",
    ))

    assert client.login_calls == 1
    assert client.location_calls != []  # search continued to the location step


# ---------------------------------------------------------------------------
# Location setter: ranking and fallback order
# ---------------------------------------------------------------------------
def test_set_location_preserves_postcode_and_ranks_max_match():
    page = FakePage(
        nodes={
            'div[data-ctx="place-loading_place-0"]': {"visible": True},
            'div[data-ctx="place-loading_place-0"] input': {"visible": True},
            MODAL_SELECTOR: {
                "visible": True,
                "texts": [
                    "Milan, 20121, IT, Lombardy, Italy, Europe, longest but wrong postcode",
                    "Roma 00131, IT",
                    "Roma 00131, IT, Lazio, Rome metropolitan area, most complete compatible record",
                ],
            },
        },
        modal_selector=MODAL_SELECTOR,
        modal_visible=lambda typed: True,
    )
    client = _client(page=page)
    # restore the real implementation (the helper stub was set in _client)
    client._set_location_field = TransEuClient._set_location_field.__get__(client, TransEuClient)

    _run(client._set_location_field(
        'div[data-ctx="place-loading_place-0"]', "IT, 00131", radius=0
    ))

    assert page.typed == ["IT, 00131"]
    assert (MODAL_SELECTOR, 2) in page.clicked
    assert (MODAL_SELECTOR, 0) not in page.clicked


def test_set_location_rus_fallback_only_after_primary_attempts():
    page = FakePage(
        nodes={
            'div[data-ctx="place-loading_place-0"]': {"visible": True},
            'div[data-ctx="place-loading_place-0"] input': {"visible": True},
            MODAL_SELECTOR: {
                "visible": True,
                "texts": ["Warszawa 00-001, PL, Mazowieckie"],
            },
        },
        modal_selector=MODAL_SELECTOR,
        modal_visible=lambda typed: bool(typed) and typed[-1].startswith("Варшава"),
    )
    client = _client(page=page)
    client._set_location_field = TransEuClient._set_location_field.__get__(client, TransEuClient)

    _run(client._set_location_field(
        'div[data-ctx="place-loading_place-0"]', "PL, 00-001, Warszawa", radius=0
    ))

    assert page.typed == ["PL, 00-001, Warszawa", "PL, 00-001", "PL", "Варшава"]
    assert (MODAL_SELECTOR, 0) in page.clicked


def test_set_location_rejects_all_incompatible_candidates():
    page = FakePage(
        nodes={
            'div[data-ctx="place-loading_place-0"]': {"visible": True},
            'div[data-ctx="place-loading_place-0"] input': {"visible": True},
            MODAL_SELECTOR: {
                "visible": True,
                "texts": ["Berlin 10115, DE", "Prague 11000, CZ"],
            },
        },
        modal_selector=MODAL_SELECTOR,
        modal_visible=lambda typed: True,
    )
    client = _client(page=page)
    client._set_location_field = TransEuClient._set_location_field.__get__(client, TransEuClient)

    with pytest.raises(ValueError, match="Location selection failed"):
        _run(client._set_location_field(
            'div[data-ctx="place-loading_place-0"]', "IT, 00131", radius=0
        ))


def test_set_location_retains_city_on_broader_fallback():
    page = FakePage(
        nodes={
            'div[data-ctx="place-loading_place-0"]': {"visible": True},
            'div[data-ctx="place-loading_place-0"] input': {"visible": True},
            MODAL_SELECTOR: {
                "visible": True,
                "texts": [
                    "Bergamo 00131, IT, Lombardy, very long unrelated city",
                    "Roma 00131, IT, Lazio",
                ],
            },
        },
        modal_selector=MODAL_SELECTOR,
        modal_visible=lambda typed: bool(typed) and typed[-1] == "IT, 00131",
    )
    client = _client(page=page)
    client._set_location_field = TransEuClient._set_location_field.__get__(client, TransEuClient)

    _run(client._set_location_field(
        'div[data-ctx="place-loading_place-0"]', "IT, 00131, Ro", radius=0
    ))

    # The dropdown only appears on the broader ISO+postcode attempt; the
    # original city signal still selects Roma (shorter) over Bergamo (longer).
    assert page.typed == ["IT, 00131, Ro", "IT, 00131"]
    assert (MODAL_SELECTOR, 1) in page.clicked
    assert (MODAL_SELECTOR, 0) not in page.clicked


# ---------------------------------------------------------------------------
# Calendar setter
# ---------------------------------------------------------------------------
def test_set_date_input_exact_iso_success():
    page = FakePage(nodes={
        'div[data-ctx="dateinput-field"] input[name="from"]': {"visible": True, "count": 1},
        'button[data-ctx="switch-mode"]': {
            "visible": True,
            "texts": ["январь 2026", "февраль 2026"],
        },
        'button[data-ctx="switch-next-page"]': {"visible": True},
        'div[data-ctx-id="2026-02-15-wrapper"]': {"visible": True, "count": 1},
    })
    client = _client(page=page)

    _run(client._set_date_input(
        page.locator(ADVANCED_SELECTOR), "from", 0, "15.02.2026"
    ))

    clicked_selectors = [sel for sel, _ in page.clicked]

    # The exact ISO day wrapper was selected exactly once (the real locator
    # click records no synthetic index, so we assert on the selector itself).
    assert clicked_selectors.count('div[data-ctx-id="2026-02-15-wrapper"]') == 1

    # The calendar advanced to the target month before the day was clicked.
    assert 'button[data-ctx="switch-next-page"]' in clicked_selectors

    # No different or fuzzy day was selected.
    assert not any(
        sel.startswith('div[data-ctx-id="') and sel != 'div[data-ctx-id="2026-02-15-wrapper"]'
        for sel in clicked_selectors
    )
    assert not any('_1d3i7nl_jh_e' in sel for sel in clicked_selectors)


def test_set_date_input_raises_on_missing_input():
    page = FakePage(nodes={})
    client = _client(page=page)

    with pytest.raises(ValueError, match="not found"):
        _run(client._set_date_input(page.locator(ADVANCED_SELECTOR), "from", 0, "15.02.2026"))


def test_set_date_input_raises_on_unparsable_header():
    page = FakePage(nodes={
        'div[data-ctx="dateinput-field"] input[name="from"]': {"visible": True, "count": 1},
        'button[data-ctx="switch-mode"]': {"visible": True, "text": "gibberish"},
    })
    client = _client(page=page)

    with pytest.raises(ValueError, match="Could not parse calendar header"):
        _run(client._set_date_input(page.locator(ADVANCED_SELECTOR), "from", 0, "15.02.2026"))


def test_set_date_input_raises_when_target_month_not_reached():
    page = FakePage(nodes={
        'div[data-ctx="dateinput-field"] input[name="from"]': {"visible": True, "count": 1},
        'button[data-ctx="switch-mode"]': {"visible": True, "text": "январь 2026"},
        'button[data-ctx="switch-next-page"]': {"visible": True},
    })
    client = _client(page=page)

    with pytest.raises(ValueError, match="was not reached"):
        _run(client._set_date_input(page.locator(ADVANCED_SELECTOR), "from", 0, "15.02.2026"))


def test_set_date_input_raises_when_day_not_found():
    page = FakePage(nodes={
        'div[data-ctx="dateinput-field"] input[name="from"]': {"visible": True, "count": 1},
        'button[data-ctx="switch-mode"]': {"visible": True, "text": "февраль 2026"},
        # no day wrapper and no day cells for 15.02.2026
    })
    client = _client(page=page)

    with pytest.raises(ValueError, match="not found"):
        _run(client._set_date_input(page.locator(ADVANCED_SELECTOR), "from", 0, "15.02.2026"))
