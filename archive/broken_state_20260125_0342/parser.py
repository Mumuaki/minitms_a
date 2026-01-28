import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class TransEuParser:
    """
    Класс для парсинга HTML-контента страницы предложений Trans.eu.
    Извлекает данные о грузах из таблицы результатов.
    """

    def parse_offers_list(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Парсит HTML основной страницы со списком предложений.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []

        # Селекторы могут меняться, поэтому используем наиболее стабильные признаки.
        # Обычно это элементы внутри контейнера результатов поиска.
        # Например, строки таблицы или div'ы с атрибутами data-ctx="offer-row" (предположительно)
        
        # На основе типовой структуры Trans.eu (примерные селекторы):
        # 1. Находим контейнер предложений
        offer_rows = soup.select('div[data-ctx^="offer-row-"]') # Предложения часто имеют ID в атрибуте
        
        if not offer_rows:
            # Попробуем альтернативный поиск по классам, если data-ctx не сработал
            offer_rows = soup.select('.offer-list-item') # Примерный класс

        logger.info(f"Found {len(offer_rows)} potential offer rows.")

        for row in offer_rows:
            try:
                offer_data = self._extract_offer_data(row)
                if offer_data:
                    offers.append(offer_data)
            except Exception as e:
                logger.error(f"Error parsing single row: {e}")
                continue

        return offers

    def _extract_offer_data(self, row_element) -> Dict[str, Any]:
        """
        Извлекает детальные данные из одного элемента (строки) предложения.
        """
        data = {}
        
        # 1. Внешний ID
        data['external_id'] = row_element.get('data-ctx', '').split('-')[-1]
        
        # 2. Места загрузки и выгрузки
        # Обычно это текстовые блоки с названиями городов и стран
        places = row_element.select('div[class*="Place__name"]')
        if len(places) >= 2:
            data['loading_place_raw'] = places[0].get_text(strip=True)
            data['unloading_place_raw'] = places[1].get_text(strip=True)
            
            # ZIP коды и страны часто рядом
            zips = row_element.select('div[class*="Place__zip"]')
            if len(zips) >= 2:
                data['loading_zip'] = zips[0].get_text(strip=True)
                data['unloading_zip'] = zips[1].get_text(strip=True)
        
        # 3. Даты
        dates = row_element.select('div[class*="Date__date"]')
        if len(dates) >= 2:
            data['loading_date_raw'] = dates[0].get_text(strip=True)
            data['unloading_date_raw'] = dates[1].get_text(strip=True)

        # 4. Вес и тип кузова
        # Часто это одна строка "24t, Tarp"
        cargo_info = row_element.select_one('div[class*="CargoInfo__info"]')
        if cargo_info:
            info_text = cargo_info.get_text(strip=True)
            data['cargo_info_raw'] = info_text

        # 5. Цена
        price_elem = row_element.select_one('div[class*="Price__amount"]')
        if price_elem:
            data['price_raw'] = price_elem.get_text(strip=True)
            
        # 6. Дистанция (если отображается)
        distance_elem = row_element.select_one('div[class*="Distance__value"]')
        if distance_elem:
            data['distance_raw'] = distance_elem.get_text(strip=True)

        return data
