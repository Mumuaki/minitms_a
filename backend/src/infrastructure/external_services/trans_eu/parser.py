"""
Parser module for Trans.eu offers.
Contains the JavaScript logic to be executed in the browser for efficient data extraction.
"""

def get_extraction_script() -> str:
    """
    Returns the JavaScript function to extract offers from the DOM.
    This script is executed via page.evaluate().
    """
    return """
    () => {
        const offers = [];
        
        // Находим все строки предложений (поддерживаем и старую, и новую верстку)
        const candidateRows = document.querySelectorAll(
            'div[data-ctx="row"], ' +
            'div[class*="LoadsListRow"], ' +
            'div[data-ctx="offer-list-item"], ' +
            'li[class*="OfferList__item"], ' + 
            'div[class*="virtuoso-item"], ' +
            'div[role="row"]' 
        );

        candidateRows.forEach(row => {
            if (row.innerText.length < 10) return;

            // 1. Places (Загрузка / Выгрузка)
            const loadingContainer = row.querySelector('[class*="loadingPlace"]');
            const unloadingContainer = row.querySelector('[class*="unloadingPlace"]');
            
            const loadingPlaceEl = loadingContainer ? loadingContainer.querySelector('[data-ctx="place"]') : null;
            const unloadingPlaceEl = unloadingContainer ? unloadingContainer.querySelector('[data-ctx="place"]') : null;
            
            const loadingPlace = loadingPlaceEl ? loadingPlaceEl.innerText.trim() : (loadingContainer ? loadingContainer.innerText.trim() : null);
            const unloadingPlace = unloadingPlaceEl ? unloadingPlaceEl.innerText.trim() : (unloadingContainer ? unloadingContainer.innerText.trim() : null);

            // 2. Dates
            const loadingDateEl = loadingContainer ? loadingContainer.querySelector('[data-ctx*="date"]') : null;
            const unloadingDateEl = unloadingContainer ? unloadingContainer.querySelector('[data-ctx*="date"]') : null;
            
            const loadingDate = loadingDateEl ? loadingDateEl.innerText.trim() : null;
            const unloadingDate = unloadingDateEl ? unloadingDateEl.innerText.trim() : null;

            // 3. Cargo Info (собираем вес, ldm и тип кузова из спанов)
            let weightText = "";
            let ldmText = "";
            let bodyParts = [];
            
            row.querySelectorAll('span').forEach(s => {
                const txt = s.innerText.trim();
                if (!txt) return;
                
                // Пропускаем служебные спаны
                if (s.getAttribute('data-test') === 'Exchange.CompanyName') return;
                if (s.getAttribute('data-ctx') === 'is-price') return;
                if (s.getAttribute('data-ctx') === 'rating') return;
                
                if (txt.includes(' т') || txt.includes(' t')) {
                    weightText = txt;
                } else if (txt.includes('ldm') || txt.includes(' LDM')) {
                    ldmText = txt;
                } else if (txt.length > 3 && !txt.includes('km') && !txt.includes('дней') && !txt.includes('€') && !txt.includes('PLN') && !txt.includes('Предложения')) {
                    if (!bodyParts.includes(txt)) {
                        bodyParts.push(txt);
                    }
                }
            });
            
            const cargoInfoParts = [];
            if (weightText) cargoInfoParts.push(weightText);
            if (bodyParts.length > 0) cargoInfoParts.push(bodyParts.join(', '));
            if (ldmText) cargoInfoParts.push(ldmText);
            const cargoInfoRaw = cargoInfoParts.join(', ');

            // 4. Price
            const priceEl = row.querySelector('[data-ctx="is-price"]') || row.querySelector('[class*="price"]');
            const price = priceEl ? priceEl.innerText.trim() : null;
            
            // 5. Distance
            const distanceEl = row.querySelector('[data-ctx="offer-requirements"]') || row.querySelector('[data-ctx="offer-distance"]');
            const distance = distanceEl ? distanceEl.innerText.trim() : null;

            // 6. Company
            const companyEl = row.querySelector('[data-test="Exchange.CompanyName"]') || row.querySelector('[class*="company"]');
            const companyName = companyEl ? companyEl.innerText.trim() : null;
            
            const ratingEl = row.querySelector('[data-ctx="rating"]');
            const companyRating = ratingEl ? ratingEl.innerText.trim() : null;

            // 7. IDs
            const externalId = row.getAttribute("data-ctx-id") || row.getAttribute("data-freightid") || row.getAttribute("id");

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
                external_id: externalId
            });
        });

        return offers;
    }
    """
