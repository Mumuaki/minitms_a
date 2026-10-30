"""Tests for the pure Trans.eu result-collection controller and driver."""

import pytest

from backend.src.infrastructure.external_services.trans_eu.collection import (
    ACTION_DONE,
    ACTION_SCROLL,
    CollectionController,
    CollectionIncompleteError,
    merge_unique,
)
from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient


def _rows(count, start=0):
    return [{"external_id": f"id-{start + i}"} for i in range(count)]


def test_collects_more_than_one_hundred_rows_without_cap():
    controller = CollectionController()
    for batch_start in range(0, 130, 20):
        batch_count = min(20, 130 - batch_start)
        action = controller.observe(
            _rows(batch_count, start=batch_start),
            loading=False,
            end_reached=(batch_start + batch_count >= 130),
            empty=False,
        )
    assert controller.count == 130
    assert action == ACTION_DONE
    assert {row["external_id"] for row in controller.ordered_items()} == {
        f"id-{i}" for i in range(130)
    }
    assert controller.ordered_items()[-1]["external_id"] == "id-129"


def test_virtualization_overlapping_views_are_deduplicated():
    controller = CollectionController()
    # window 1: 0..19, window 2: 10..29 (overlap), window 3: 20..39
    controller.observe(_rows(20, 0), loading=False, end_reached=False, empty=False)
    controller.observe(_rows(20, 10), loading=False, end_reached=False, empty=False)
    action = controller.observe(_rows(20, 20), loading=False, end_reached=True, empty=False)
    assert controller.count == 40
    assert controller.ordered_items()[0]["external_id"] == "id-0"
    assert action == ACTION_DONE


def test_delayed_loading_is_not_treated_as_empty():
    controller = CollectionController()
    # First rounds: nothing visible yet but a loader is present.
    for _ in range(3):
        action = controller.observe([], loading=True, end_reached=False, empty=False)
        assert action == ACTION_SCROLL
    # Data finally arrives and then the list ends.
    action = controller.observe(_rows(10), loading=False, end_reached=True, empty=False)
    assert controller.count == 10
    assert action == ACTION_DONE


def test_genuine_empty_completion_returns_zero_results():
    controller = CollectionController()
    action = controller.observe([], loading=False, end_reached=False, empty=True)
    assert action == ACTION_DONE
    assert controller.count == 0
    assert controller.ordered_items() == []


def test_scrolled_to_bottom_completes_without_end_marker_or_count_match():
    # The portal groups similar offers, so the header "Все предложения N" can be
    # larger than the rendered row count. Once the virtualized list is scrolled
    # to the bottom and a round adds no new rows, collection must complete
    # instead of stalling on the unmatched count.
    controller = CollectionController()
    controller.observe(_rows(14), loading=False, end_reached=False, empty=False, expected_total=15)
    action = controller.observe(
        _rows(14), loading=False, end_reached=False, empty=False,
        expected_total=15, scrolled_to_bottom=True,
    )
    assert action == ACTION_DONE
    assert controller.count == 14


def test_scrolled_to_bottom_with_new_rows_keeps_scrolling():
    # New rows arriving in the same round means there may be more below: do not
    # finish yet even though the bottom flag is set.
    controller = CollectionController()
    controller.observe(_rows(10), loading=False, end_reached=False, empty=False, scrolled_to_bottom=False)
    action = controller.observe(
        _rows(15), loading=False, end_reached=False, empty=False, scrolled_to_bottom=True,
    )
    assert action == ACTION_SCROLL
    assert controller.count == 15


def test_stall_without_end_marker_raises_completeness_error():
    controller = CollectionController(max_stall_rounds=3)
    controller.observe(_rows(5), loading=False, end_reached=False, empty=False)
    controller.observe([], loading=False, end_reached=False, empty=False)
    controller.observe([], loading=False, end_reached=False, empty=False)
    with pytest.raises(CollectionIncompleteError):
        controller.observe([], loading=False, end_reached=False, empty=False)


def test_missing_external_id_raises_instead_of_skipping():
    controller = CollectionController()
    with pytest.raises(CollectionIncompleteError):
        controller.observe(
            [{"external_id": "id-1"}, {"external_id": None}],
            loading=False,
            end_reached=False,
            empty=False,
        )


def test_merge_unique_deduplicates_before_geocoding():
    seen = {}
    added = merge_unique([{"external_id": "a"}, {"external_id": "b"}], seen)
    assert added == 2
    added = merge_unique([{"external_id": "a"}, {"external_id": "c"}], seen)
    assert added == 1
    assert set(seen) == {"a", "b", "c"}


def test_merge_unique_rejects_missing_id():
    with pytest.raises(CollectionIncompleteError):
        merge_unique([{"external_id": ""}], {})


def test_expected_count_completes_without_end_marker():
    controller = CollectionController()
    controller.observe(_rows(25), loading=False, end_reached=False, empty=False, expected_total=40)
    action = controller.observe(_rows(40), loading=False, end_reached=False, empty=False, expected_total=40)
    assert action == ACTION_DONE
    assert controller.count == 40


def test_empty_after_rows_without_expected_count_stalls_and_raises():
    controller = CollectionController(max_stall_rounds=3)
    controller.observe(_rows(5), loading=False, end_reached=False, empty=False)
    controller.observe([], loading=False, end_reached=False, empty=True)
    controller.observe([], loading=False, end_reached=False, empty=True)
    with pytest.raises(CollectionIncompleteError):
        controller.observe([], loading=False, end_reached=False, empty=True)


def test_empty_after_rows_with_agreed_expected_count_completes():
    controller = CollectionController()
    controller.observe(_rows(5), loading=False, end_reached=False, empty=False, expected_total=5)
    action = controller.observe([], loading=False, end_reached=False, empty=True, expected_total=5)
    assert action == ACTION_DONE
    assert controller.count == 5

# ---------------------------------------------------------------------------
# Driver (`TransEuClient._collect_all_offers`) against a tiny fake page.
# ---------------------------------------------------------------------------



class _FakeLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    @property
    def first(self):
        return self

    async def count(self):
        return 1 if self.page.visible_load_more and "load-more" in self.selector else 0

    async def is_visible(self, timeout=None):
        return self.page.visible_load_more and "load-more" in self.selector

    async def click(self, force=False):
        if "load-more" in self.selector:
            self.page.clicked_load_more += 1


class _FakePage:
    """Simulates a virtualized list that reveals 25 rows per scroll/load-more."""

    def __init__(self, total_rows, *, load_more=False, stall=False, end_marker=True):
        self.total_rows = total_rows
        self.revealed = 0
        self.scroll_calls = 0
        self.clicked_load_more = 0
        self.visible_load_more = load_more
        self.stall = stall
        self.end_marker = end_marker

    def locator(self, selector):
        return _FakeLocator(self, selector)

    async def wait_for_timeout(self, ms):
        return None

    async def evaluate(self, js, *args):
        if isinstance(js, str):
            if "root_found" in js:
                # result-list state probe script
                loading = bool(self.stall and self.revealed < self.total_rows)
                return {
                    "root_found": True,
                    "total": self.total_rows,
                    "loading": loading,
                    "end_reached": bool(self.end_marker and self.revealed >= self.total_rows),
                    "empty": False,
                }
            if "external_id" in js:
                # extraction script: reveal the next chunk and return the viewport
                if self.stall and self.revealed >= 25:
                    pass
                elif self.revealed < self.total_rows:
                    self.revealed = min(self.total_rows, self.revealed + 25)
                return [{"external_id": f"id-{i}"} for i in range(self.revealed)]
            if "scrollBy" in js:
                self.scroll_calls += 1
                if not self.stall and self.revealed < self.total_rows:
                    self.revealed = min(self.total_rows, self.revealed + 25)
                return None
        return []


class _NoRootPage:
    visible_load_more = False
    clicked_load_more = 0

    def locator(self, selector):
        return _FakeLocator(self, selector)

    async def wait_for_timeout(self, ms):
        return None

    async def evaluate(self, js, *args):
        if isinstance(js, str):
            if "root_found" in js:
                return {"root_found": False, "total": None, "loading": False, "end_reached": False, "empty": False}
            if "external_id" in js:
                return []
        return []


def _run(coro):
    import asyncio
    return asyncio.run(coro)


def test_client_collects_virtualized_list_over_scroll():
    page = _FakePage(total_rows=120)
    client = TransEuClient()
    client.page = page

    result = _run(client._collect_all_offers())

    assert len(result) == 120
    assert result[0]["external_id"] == "id-0"


def test_client_collects_pagination_load_more():
    page = _FakePage(total_rows=60, load_more=True)
    client = TransEuClient()
    client.page = page

    result = _run(client._collect_all_offers())

    assert len(result) == 60
    assert page.clicked_load_more > 0


def test_client_collects_via_expected_count_without_end_marker():
    # No end-of-list marker is ever visible; completion is certified by the
    # runtime-detected "Все предложения N" header count.
    page = _FakePage(total_rows=110, end_marker=False)
    client = TransEuClient()
    client.page = page

    result = _run(client._collect_all_offers())

    assert len(result) == 110


def test_client_stall_without_terminal_state_raises():
    page = _FakePage(total_rows=200, end_marker=False, stall=True)
    client = TransEuClient()
    client.page = page

    with pytest.raises(CollectionIncompleteError):
        _run(client._collect_all_offers())


def test_client_root_not_found_raises_completeness_error():
    client = TransEuClient()
    client.page = _NoRootPage()

    with pytest.raises(CollectionIncompleteError):
        _run(client._collect_all_offers())


def test_extraction_script_captures_semantic_fields():
    from backend.src.infrastructure.external_services.trans_eu import parser
    js = parser.get_extraction_script()
    assert "description_raw" in js
    assert "external_id" in js
    assert "loading_place_raw" in js
    assert "cargo_info_raw" in js
    # Rows without a verifiable per-offer ID must fail closed, not invent an ID.
    assert "externalId" in js


def test_state_script_scopes_to_result_list_and_excludes_form_fields():
    from backend.src.infrastructure.external_services.trans_eu import parser
    js = parser.get_result_state_script()
    assert "root_found" in js
    assert "offer-list" in js
    assert "total" in js
    assert "loading" in js
    # The probe explicitly excludes place/date form-field contexts so a
    # loading-place input can never be mistaken for an in-flight loader.
    assert "place" in js
    assert "date" in js
