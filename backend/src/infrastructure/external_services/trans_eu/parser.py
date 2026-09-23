"""
Parser module for Trans.eu offers.
Contains the JavaScript logic to be executed in the browser for efficient data extraction.
"""

def get_extraction_script() -> str:
    """
    Returns the JavaScript function to extract offers from the DOM.
    Pass 1: reads the offers list rows (places, dates, distance, cargo info, price, company).
    Pass 2: opens the details drawer for every offer and reads the additional description
            from the "Подробности" (offer-details) tab.
    """
    return """
    async () => {
        const NL = String.fromCharCode(10);
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

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

            // 2. Dates
            const loadingDateEl = row.querySelector('[data-ctx="loading-place-cell-date"]');
            const unloadingDateEl = row.querySelector('[data-ctx="unloading-place-cell-date"]');
            let loadingDate = null;
            let unloadingDate = null;
            if (loadingDateEl) {
                const lines = loadingDateEl.innerText.split(NL).map(x => x.trim());
                loadingDate = lines.find(x => /\d{2}\.\d{2}/.test(x)) || loadingDateEl.innerText.trim();
            }
            if (unloadingDateEl) {
                const lines = unloadingDateEl.innerText.split(NL).map(x => x.trim());
                unloadingDate = lines.find(x => /\d{2}\.\d{2}/.test(x)) || unloadingDateEl.innerText.trim();
            }

            // 3. Distance (km)
            const distEl = row.querySelector('[data-ctx="loading-place-cell-distance"]');
            const distance = distEl ? distEl.innerText.trim() : null;

            // 4. Cargo info: вес + тип кузова
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
                description_raw: null,
                offer_url: null,
                external_id: externalId
            });
        });

        // PASS 2: «Дополнительное описание» + ссылка на карточку из drawer
        const rowEls = Array.from(document.querySelectorAll('div[data-ctx="row"]'));
        for (let i = 0; i < rowEls.length; i++) {
            const row = rowEls[i];
            let extId = null;
            row.querySelectorAll('[data-ctx]').forEach(el => {
                const c = el.getAttribute('data-ctx');
                if (c && /^\d+-\d+$/.test(c) && !extId) extId = c;
            });
            if (!extId) continue;
            try {
                row.click();
                await sleep(1500);
                const offerUrl = location.href;
                const tab = document.querySelector('button[data-ctx-id="offer-details"]');
                if (tab) { tab.click(); await sleep(500); }
                let desc = null;
                const tc = document.querySelector('[data-ctx="tabContent"]');
                if (tc) {
                    const txt = tc.innerText || '';
                    const start = txt.indexOf('Дополнительное описание');
                    if (start >= 0) {
                        let rest = txt.slice(start + 'Дополнительное описание'.length);
                        const end = rest.indexOf('Основная информация');
                        if (end > 0) rest = rest.slice(0, end);
                        desc = rest.split(NL).map(x => x.trim()).filter(Boolean).join(' ');
                    }
                }
                const offer = offers.find(o => o.external_id === extId);
                if (offer) {
                    if (desc) offer.description_raw = desc.slice(0, 500);
                    if (offerUrl) offer.offer_url = offerUrl.slice(0, 600);
                }
            } catch (e) { /* skip this offer */ }
        }

        return offers;
    }
    """
