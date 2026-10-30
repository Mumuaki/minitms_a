"""Pure, Playwright-free Trans.eu result-collection logic.

``client.py`` drives the browser (scrolling, clicking load-more, waiting for
the loader) and this module makes the *decisions*: deduplication, stall
detection, empty/end validation and completeness. It has no side effects and
is exercised offline with fixtures that prove >50 and >100 rows, virtualized
overlapping views, pagination, delayed loading, stalls/errors and a genuine
empty completion.

Completeness contract (fail-closed):

* there is **no** arbitrary total-rows/page/scroll cap;
* a bounded number of stalled/loading rounds is allowed; if the list still has
  not reached a verified end/empty state after that bound, collection raises
  :class:`CollectionIncompleteError` instead of returning a truncated success;
* a transient empty viewport is never mistaken for a zero-result completion;
* an extracted offer row without a stable external ID is never silently
  skipped — it raises immediately (the caller must fix mapping, not drop rows).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CollectionIncompleteError(RuntimeError):
    """Raised when collection cannot reach a verified end/empty state."""


# Number of consecutive rounds without progress before a run is declared
# incomplete. This bounds *stalling*, not the total number of offers.
MAX_STALL_ROUNDS = 12

# Actions the driver (client.py) is asked to perform next.
ACTION_SCROLL = "scroll"
ACTION_LOAD_MORE = "load_more"
ACTION_DONE = "done"


@dataclass
class CollectionController:
    """Tracks unique rows and decides the next collection step.

    Rows are keyed by their stable ``external_id``; the first occurrence wins
    (order is preserved) so repeated/overlapping virtualized views and
    re-loading pages never produce duplicates.
    """

    max_stall_rounds: int = MAX_STALL_ROUNDS
    _seen: Dict[str, dict] = field(default_factory=dict, init=False)
    _order: List[dict] = field(default_factory=list, init=False)
    _stall_rounds: int = field(default=0, init=False)
    _had_rows: bool = field(default=False, init=False)

    def observe(
        self,
        rows: list,
        *,
        loading: bool,
        end_reached: bool,
        empty: bool,
        expected_total=None,
        scrolled_to_bottom: bool = False,
    ) -> str:
        """Record one extraction round and return the next action.

        ``rows`` is the raw list from the parser for the current viewport.
        ``loading`` signals an in-flight loader (never treated as empty/end).
        ``end_reached`` signals a verified end-of-list marker scoped to the
        result list. ``empty`` signals a verified empty-list state (result
        container present, zero items). ``expected_total`` is the optional
        runtime-detected "All offers / Все предложения N" header count.
        ``scrolled_to_bottom`` reports that the virtualized list has been
        scrolled to its end — a reliable completion signal even when the
        header count exceeds the rendered row count (the portal groups similar
        offers, so the two need not match).

        Raises :class:`CollectionIncompleteError` for missing offer IDs and for
        stalling without a verified terminal state.
        """
        added = 0
        for row in rows:
            if not isinstance(row, dict):
                raise CollectionIncompleteError(
                    "Collection failed: extracted a non-mapping offer row"
                )
            external_id = row.get("external_id")
            if not isinstance(external_id, str) or not external_id.strip():
                raise CollectionIncompleteError(
                    "Collection failed: offer row is missing a stable external ID"
                )
            if external_id not in self._seen:
                self._seen[external_id] = row
                self._order.append(row)
                added += 1

        if added > 0:
            self._had_rows = True
            self._stall_rounds = 0
        else:
            self._stall_rounds += 1

        # Normalize the runtime-detected expected total (None means unknown).
        expected = None
        if not isinstance(expected_total, bool) and isinstance(expected_total, (int, float)):
            expected = int(expected_total)

        if not loading:
            # Explicit verified end-of-list marker finishes the run.
            if end_reached:
                return ACTION_DONE
            # Runtime-detected header count reached: all unique offers collected.
            if expected is not None and self.count >= expected:
                return ACTION_DONE
            # The virtualized list has been scrolled to its end and produced no
            # new rows this round: it is complete. This is the authoritative
            # signal when the header count exceeds the rendered row count (the
            # portal groups similar offers, so the two need not match).
            if scrolled_to_bottom and self._had_rows and added == 0:
                return ACTION_DONE
            if empty:
                # A genuine zero-result completion only when no rows were seen.
                if not self._had_rows:
                    return ACTION_DONE
                # Empty after rows contradicts completeness unless the expected
                # count agrees; otherwise treat it as a transient state.
                if expected is not None and self.count >= expected:
                    return ACTION_DONE

        # Nothing new and no verified terminal state: bounded retry, then fail.
        if self._stall_rounds >= self.max_stall_rounds:
            raise CollectionIncompleteError(
                "Collection incomplete: results stopped changing without an "
                "end-of-list marker or a verified expected-count match"
            )

        return ACTION_SCROLL

    @property
    def had_rows(self) -> bool:
        """True once at least one unique offer row has been observed."""
        return self._had_rows

    @property
    def count(self) -> int:
        return len(self._order)

    def ordered_items(self) -> list:
        """Return the collected unique rows in first-seen order."""
        return list(self._order)


def merge_unique(rows: list, seen: Dict[str, dict]) -> int:
    """Merge ``rows`` into ``seen`` (external_id -> row); return rows added.

    Kept as a standalone helper for the in-process deduplication that must run
    before expensive geocoding. Rows without a stable external ID raise
    :class:`CollectionIncompleteError` (never silently dropped).
    """
    added = 0
    for row in rows:
        if not isinstance(row, dict):
            raise CollectionIncompleteError("Invalid offer row: not a mapping")
        external_id = row.get("external_id")
        if not isinstance(external_id, str) or not external_id.strip():
            raise CollectionIncompleteError("Invalid offer row: missing stable external ID")
        if external_id not in seen:
            seen[external_id] = row
            added += 1
    return added
