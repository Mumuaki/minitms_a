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
        
        // Strategy: Look for offer list items.
        // Trans.eu usually uses a Virtual List or standard list.
        // We look for elements that look like offer cards.
        
        // Potential selectors for the list container or items
        // We prioritize data-ctx if available, otherwise generic classes.
        
        // Try to find all potential offer rows
        // Using a broad selector to catch the rows
        const candidateRows = document.querySelectorAll(
            'div[data-ctx="offer-list-item"], ' +
            'li[class*="OfferList__item"], ' + 
            'div[class*="virtuoso-item"], ' +
            'div[role="row"]' 
        );

        candidateRows.forEach(row => {
            // Helper to safe-get text
            const getText = (ctx, fallbackSelector) => {
                let el = null;
                if (ctx) el = row.querySelector(`[data-ctx="${ctx}"]`);
                if (!el && fallbackSelector) el = row.querySelector(fallbackSelector);
                return el ? el.innerText.trim() : null;
            };

            // Helper for attributes
            const getAttr = (selector, attr) => {
                const el = row.querySelector(selector);
                return el ? el.getAttribute(attr) : null;
            };

            // Only process if it looks like content (has text)
            if (row.innerText.length < 10) return;

            // --- EXTRACT FIELDS ---
            
            // 1. Places (Loading / Unloading)
            // Often structured as "City, Country" or separate fields
            const loadingPlace = getText("offer-place-loading") || getText(null, '[class*="loading"]');
            const unloadingPlace = getText("offer-place-unloading") || getText(null, '[class*="unloading"]');

            // 2. Dates
            const loadingDate = getText("offer-date-loading") || getText(null, '[class*="date"]');
            const unloadingDate = getText("offer-date-unloading"); // Might be same container?

            // 3. Cargo Info (Weight, Body)
            const cargoInfo = getText("offer-cargo-info") || getText(null, '[class*="cargo"]');
            
            // 4. Price
            const price = getText("offer-rate") || getText(null, '[class*="price"]');
            
            // 5. Distance
            const distance = getText("offer-distance");

            // 6. Company
            const companyName = getText("company-name") || getText(null, '[class*="company"]');
            const companyRating = getText("company-rating");

            // 7. IDs
            const externalId = row.getAttribute("id") || row.getAttribute("data-id") || getAttr('[data-offer-id]', 'data-offer-id');

            // Push raw object
            offers.push({
                loading_place_raw: loadingPlace,
                unloading_place_raw: unloadingPlace,
                loading_date_raw: loadingDate,
                unloading_date_raw: unloadingDate,
                cargo_info_raw: cargoInfo,
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
