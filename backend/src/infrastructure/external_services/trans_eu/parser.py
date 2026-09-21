"""
Parser module for Trans.eu offers.
Contains the JavaScript logic to be executed in the browser for efficient data extraction.
"""

def get_extraction_script() -> str:
    """
    Returns the JavaScript function to extract offers from the DOM.
    Uses the actual data-ctx attributes of the Trans.eu offers list.
    """
    return """
    () => {
        const offers = [];
        const rows = document.querySelectorAll('div[data-ctx="row"]');

        rows.forEach(row => {
            const text = row.innerText;
            if (text.length < 10) return;

            // 1. Places
            const loadingEl = row.querySelector('[data-ctx="loading-place-cell"] [data-ctx="place"]')
                || row.querySelector('[data-ctx="loading-place-cell"]');
            const unloadingEl = row.querySelector('[data-ctx="unloading-place-cell"] [data-ctx="place"]')
                || row.querySelector('[data-ctx="unloading-place-cell"]');
            const loadingPlace = loadingEl ? loadingEl.innerText.trim() : null;
            const unloadingPlace = unloadingEl ? unloadingEl.innerText.trim() : null;

            // 2. Dates (ячейка содержит место + дату — берём строку с датой)
            const loadingDateEl = row.querySelector('[data-ctx="loading-place-cell-date"]');
            const unloadingDateEl = row.querySelector('[data-ctx="unloading-place-cell-date"]');
            let loadingDate = null;
            let unloadingDate = null;
            if (loadingDateEl) {
                const lines = loadingDateEl.innerText.split(String.fromCharCode(10)).map(x => x.trim());
                loadingDate = lines.find(x => /\d{2}\.\d{2}/.test(x)) || loadingDateEl.innerText.trim();
            }
            if (unloadingDateEl) {
                const lines = unloadingDateEl.innerText.split(String.fromCharCode(10)).map(x => x.trim());
                unloadingDate = lines.find(x => /\d{2}\.\d{2}/.test(x)) || unloadingDateEl.innerText.trim();
            }

            // 3. Distance (км)
            const distEl = row.querySelector('[data-ctx="loading-place-cell-distance"]');
            const distance = distEl ? distEl.innerText.trim() : null;

            // 4. Cargo info: вес + тип кузова (Грузоподъёмность + Тип ТС)
            const infoEl = row.querySelector('[data-ctx="offer-info-cell-properties"]');
            const cargoInfoRaw = infoEl ? infoEl.innerText.trim() : '';

            // 5. Price
            const priceEl = row.querySelector('[data-ctx="is-price"]');
            const price = priceEl ? priceEl.innerText.trim() : null;

            // 6. Company + rating
            const companyEl = row.querySelector('[data-ctx="personName"]') || row.querySelector('[data-ctx="shipper-cell"]');
            const companyName = companyEl ? companyEl.innerText.trim() : null;
            const ratingEl = row.querySelector('[data-ctx="rating"]');
            const companyRating = ratingEl ? ratingEl.innerText.trim() : null;

            // 7. External id (numeric data-ctx like "1079543-12")
            let externalId = null;
            row.querySelectorAll('[data-ctx]').forEach(el => {
                const ctx = el.getAttribute('data-ctx');
                if (ctx && /^\d+-\d+$/.test(ctx) && !externalId) externalId = ctx;
            });

            offers.push({
                loading_place_raw: loadingPlace,
                unloading_place_raw: unloadingPlace,
                loading_date_raw: loadingDate,
                unloading_date_raw: unloadingDate,
                cargo_info_raw: cargoInfoRaw,
                price_raw: price,
                distance_raw: distance,
                company_name: companyName,
                company_rating_raw: companyRating,
                published_at_raw: null,
                external_id: externalId
            });
        });

        return offers;
    }
    """
