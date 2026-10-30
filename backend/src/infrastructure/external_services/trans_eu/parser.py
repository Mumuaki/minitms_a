"""
Parser module for Trans.eu offers.

Contains the JavaScript logic executed in the browser for data extraction.

The live portal renders each offer as ``div[data-ctx="row"]`` inside
``div[data-ctx="LoadsList.container"]``. The row carries a stable
``data-freightid`` and its cells expose stable ``data-ctx`` markers
(``loading-place-cell-date``, ``unloading-place-cell-date``,
``offer-info-cell-properties``, ``is-price``, ``rating``, ``dateCell``,
``hourCell``) even though the CSS classes are obfuscated. Extraction therefore
targets these markers, not class names.

Field-capture contract (fail-closed):

* ``description_raw`` distinguishes an UNAVAILABLE description (``null``: no
  dedicated description element was found) from a present, known-empty
  description (``""``). Callers must not treat ``null`` as verified clean.
* ``external_id`` is only taken from verifiable per-offer attributes; a row
  without a stable offer ID yields ``external_id: null`` so the collection
  controller fails closed instead of silently dropping the row.
* Cargo info is taken from the dedicated ``offer-info-cell-properties`` marker,
  never from the whole row, so route/price/company text cannot pollute body
  semantics.
"""


def get_extraction_script() -> str:
    """Return the JavaScript function to extract offers from the DOM.

    This script is executed via page.evaluate().
    """
    return r"""
    () => {
        const offers = [];
        const clean = (t) => (t || '').trim().replace(/\s+/g, ' ');

        // Split "PL 05-410 Józefów 29.10, 15:00 30.10, 18:00" into {place, date}.
        // Used for the loading cell, whose place and dates are not wrapped in
        // separate [data-ctx] markers (unlike the unloading cell).
        const splitPlaceDate = (text) => {
            const m = text.match(/^(.*?)\s+(\d{1,2}\.\d{1,2}.*)$/);
            if (!m) return { place: text, date: null };
            return { place: clean(m[1]), date: clean(m[2]) };
        };

        const rows = document.querySelectorAll('div[data-ctx="row"]');
        for (const row of rows) {
            if ((row.innerText || '').length < 10) continue;

            const externalId =
                row.getAttribute('data-freightid') ||
                row.getAttribute('data-offer-id') ||
                row.getAttribute('data-load-id') ||
                row.getAttribute('data-loadid') ||
                null;

            // 1. Places and dates.
            const loadingCell = row.querySelector('[data-ctx="loading-place-cell-date"]');
            const unloadingCell = row.querySelector('[data-ctx="unloading-place-cell-date"]');

            let loadingPlace = null, loadingDate = null;
            if (loadingCell) {
                const placeEl = loadingCell.querySelector('[data-ctx="place"]');
                const dateEl = loadingCell.querySelector('[data-ctx="dates"]');
                if (placeEl) {
                    loadingPlace = clean(placeEl.innerText);
                    loadingDate = dateEl ? clean(dateEl.innerText) : null;
                } else {
                    const s = splitPlaceDate(clean(loadingCell.innerText));
                    loadingPlace = s.place || null;
                    loadingDate = s.date;
                }
            }

            let unloadingPlace = null, unloadingDate = null;
            if (unloadingCell) {
                const placeEl = unloadingCell.querySelector('[data-ctx="place"]');
                const dateEl = unloadingCell.querySelector('[data-ctx="dates"]');
                if (placeEl) {
                    unloadingPlace = clean(placeEl.innerText);
                    unloadingDate = dateEl ? clean(dateEl.innerText) : null;
                } else {
                    const s = splitPlaceDate(clean(unloadingCell.innerText));
                    unloadingPlace = s.place || null;
                    unloadingDate = s.date;
                }
            }

            // 2. Cargo info from the dedicated marker only.
            const propsEl = row.querySelector('[data-ctx="offer-info-cell-properties"]');
            const cargoInfoRaw = propsEl ? (clean(propsEl.innerText) || null) : null;

            // 3. Distance + description: the vehicle-info cell holds two ellipsis
            // nodes — one carries "NNN km …", the other the free-text remarks.
            let distanceRaw = null, descriptionRaw = null;
            const vehicleInfo = row.querySelector('[class*="vehicleInfo"]');
            if (vehicleInfo) {
                const ellipses = vehicleInfo.querySelectorAll('[data-ctx="ellipsis"]');
                const descParts = [];
                for (const el of ellipses) {
                    const t = clean(el.innerText);
                    if (!t) continue;
                    if (t === cargoInfoRaw) continue;  // cargo props duplicated in an ellipsis
                    if (distanceRaw === null && /km\b|км\b/i.test(t)) {
                        distanceRaw = t;
                    } else {
                        descParts.push(t);
                    }
                }
                if (descParts.length) descriptionRaw = descParts.join(' | ');
            }

            // 4. Price (dash means no price set).
            const priceEl = row.querySelector('[data-ctx="is-price"]');
            const price = priceEl ? clean(priceEl.innerText) : null;

            // 5. Company / rating / publication time.
            const companyEl = row.querySelector('[data-test="Exchange.CompanyName"]');
            const companyName = companyEl ? clean(companyEl.innerText) : null;
            const ratingEl = row.querySelector('[data-ctx="rating"]');
            const companyRating = ratingEl ? clean(ratingEl.innerText) : null;

            const dateEl = row.querySelector('[data-ctx="dateCell"]');
            const hourEl = row.querySelector('[data-ctx="hourCell"]');
            let publishedAt = null;
            if (dateEl) {
                publishedAt = clean(dateEl.innerText);
                if (hourEl) publishedAt += ' ' + clean(hourEl.innerText);
            }

            offers.push({
                loading_place_raw: loadingPlace,
                unloading_place_raw: unloadingPlace,
                loading_date_raw: loadingDate,
                unloading_date_raw: unloadingDate,
                cargo_info_raw: cargoInfoRaw,
                description_raw: descriptionRaw,
                price_raw: price,
                distance_raw: distanceRaw,
                company_name: companyName,
                company_rating_raw: companyRating,
                published_at_raw: publishedAt,
                external_id: externalId
            });
        }

        return offers;
    }
    """


def get_result_state_script() -> str:
    """Return JS that probes the verified result-list state.

    The probe is scoped to the result list (never the whole page), so form
    fields such as ``place-loading_place-0`` cannot be mistaken for an
    in-flight loader. It returns ``{root_found, total, loading, end_reached,
    empty, scrolled_to_bottom}`` where ``total`` is the runtime-detected
    "Все предложения / All offers N" header count (or ``null``), and
    ``scrolled_to_bottom`` reports whether the virtualized list has been
    scrolled to its end.
    """
    return r"""
    () => {
        const isVisible = (el) => {
            if (!el) return false;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return false;
            const s = getComputedStyle(el);
            return s.visibility !== 'hidden' && s.display !== 'none';
        };

        const ROOT_SELECTORS = [
            'div[data-ctx="LoadsList.container"]',
            'div[data-ctx="offer-list"]',
            'div[data-ctx="offers-list"]',
            'div[data-ctx="result-list"]',
            'div[data-ctx="offers"]',
            'ul[data-ctx="offer-list"]',
            '[data-testid="offers-list"]',
            'div[class*="OffersList"]',
            'div[class*="offers-list"]',
            'div[class*="offer-list"]',
            'div[class*="OfferList"]',
        ];
        let root = null;
        for (const s of ROOT_SELECTORS) {
            const el = document.querySelector(s);
            if (el) { root = el; break; }
        }
        if (!root) {
            return { root_found: false, total: null, loading: false, end_reached: false, empty: false, scrolled_to_bottom: false };
        }

        // Total offer count from the header text ("Все предложения 1234").
        let total = null;
        const labelRe = /(?:все предложения|всего предложений|предложений|all offers|wszystkie oferty|oferty|wyniki?)\s*:?\s*([0-9][0-9\s\u00a0.,]*)/i;
        const headerNodes = root.querySelectorAll('h1,h2,h3,h4,h5,h6,div,span,p');
        for (const el of headerNodes) {
            const text = (el.innerText || '').trim();
            if (!text || text.length > 240) continue;
            const m = text.match(labelRe);
            if (m) {
                const digits = m[1].replace(/[\s\u00a0,]/g, '').replace(/\./g, '');
                if (digits && /^\d+$/.test(digits)) {
                    const n = parseInt(digits, 10);
                    if (!isNaN(n)) { total = n; break; }
                }
            }
        }

        // In-flight loader/spinner scoped to the result list and excluding
        // form fields so loading-place/date inputs can never be a loader.
        let loading = false;
        const LOADER_SELECTORS = ['[data-ctx*="loading"]', '[data-ctx*="spinner"]', '[class*="loader"]', '[class*="spinner"]'];
        outer: for (const s of LOADER_SELECTORS) {
            for (const el of root.querySelectorAll(s)) {
                if (!isVisible(el)) continue;
                const ctx = (el.getAttribute('data-ctx') || '').toLowerCase();
                if (ctx.includes('place') || ctx.includes('date') || ctx.includes('form') || ctx.includes('input')) continue;
                if (el.closest('input, select, textarea, button, form, [data-ctx*="place"], [data-ctx*="date"]')) continue;
                loading = true;
                break outer;
            }
        }

        let end_reached = false;
        const END_SELECTORS = ['[data-ctx*="list-end"]', '[data-ctx*="end-of-list"]', '[data-ctx*="no-more-results"]', '[data-ctx*="list-end-marker"]'];
        for (const s of END_SELECTORS) {
            for (const el of root.querySelectorAll(s)) {
                if (isVisible(el)) { end_reached = true; break; }
            }
            if (end_reached) break;
        }

        let empty = false;
        const EMPTY_SELECTORS = ['[data-ctx*="empty"]', '[data-ctx*="no-results"]', '[data-ctx*="empty-results"]'];
        for (const s of EMPTY_SELECTORS) {
            for (const el of root.querySelectorAll(s)) {
                if (isVisible(el)) { empty = true; break; }
            }
            if (empty) break;
        }

        // Whether the virtualized list has been scrolled to its end. The portal
        // renders rows lazily inside an inner scrollable container (div[data-ctx="LoadsList"]),
        // so we locate the first scrollable ancestor of the last row and check
        // its scroll position. This is the reliable completion signal: the header
        // "Все предложения N" counts offers while the portal groups similar
        // offers, so the rendered row count can be smaller than N.
        let scrolled_to_bottom = false;
        {
            const rows = root.querySelectorAll('div[data-ctx="row"]');
            if (rows.length) {
                let el = rows[rows.length - 1];
                while (el && el !== document.body && el !== document.documentElement
                       && el.scrollHeight <= el.clientHeight + 1) {
                    el = el.parentElement;
                }
                if (el && el !== document.body && el !== document.documentElement) {
                    scrolled_to_bottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 2;
                } else {
                    scrolled_to_bottom = (window.innerHeight + window.scrollY) >= document.body.scrollHeight - 2;
                }
            }
        }

        return { root_found: true, total: total, loading: loading, end_reached: end_reached, empty: empty, scrolled_to_bottom: scrolled_to_bottom };
    }
    """
