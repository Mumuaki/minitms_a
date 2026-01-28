import re
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple

from backend.src.domain.entities.cargo import Cargo, CargoStatusColor

logger = logging.getLogger(__name__)

class TransEuMapper:
    """
    Класс для трансформации сырых данных от парсера в доменные сущности Cargo.
    Обеспечивает очистку данных, парсинг чисел, дат и типов.
    """
    
    def map_to_cargo(self, raw_data: Dict[str, Any]) -> Cargo:
        """
        Преобразует словарь с сырыми данными в объект Cargo.
        """
        try:
            cargo = Cargo(
                external_id=raw_data.get('external_id'),
                source="trans.eu"
            )
            
            # 1. Маппинг мест
            loading_raw = raw_data.get('loading_place_raw', '')
            unloading_raw = raw_data.get('unloading_place_raw', '')
            
            cargo.loading_place = {
                "city": self._clean_city_name(loading_raw),
                "zip": raw_data.get('loading_zip', ''),
                "country": self._extract_country(loading_raw),
            }
            
            cargo.unloading_place = {
                "city": self._clean_city_name(unloading_raw),
                "zip": raw_data.get('unloading_zip', ''),
                "country": self._extract_country(unloading_raw),
            }
            
            # 2. Парсинг дат
            cargo.loading_date = self._parse_date(raw_data.get('loading_date_raw'))
            cargo.unloading_date = self._parse_date(raw_data.get('unloading_date_raw'))
            
            # 3. Парсинг веса и кузова
            weight, body_type = self._parse_cargo_info(raw_data.get('cargo_info_raw'))
            cargo.weight = weight
            cargo.body_type = body_type
            
            # 4. Парсинг цены
            cargo.price = self._parse_price(raw_data.get('price_raw'))
            
            # 5. Парсинг дистанции (Trans.eu distance)
            cargo.distance_trans_eu = self._parse_int(raw_data.get('distance_raw'))
            
            # Инициализация дополнительных полей
            cargo.is_hidden = False
            cargo.status_color = CargoStatusColor.GRAY
            
            return cargo
            
        except Exception as e:
            logger.error(f"Mapping failed for external_id {raw_data.get('external_id')}: {e}")
            raise e

    def _clean_city_name(self, text: str) -> str:
        if not text: return ""
        # Удаляем код страны в скобках, например "Warszawa (PL)" -> "Warszawa"
        return re.sub(r'\s*\([A-Z]{2}\)', '', text).strip()

    def _extract_country(self, place_text: str) -> str:
        if not place_text: return ""
        # Ищем код страны в скобках
        match = re.search(r'\(([A-Z]{2})\)', place_text)
        if match:
            return match.group(1)
        return ""

    def _parse_date(self, date_str: str) -> Optional[date]:
        if not date_str: return None
        try:
            # Ожидаем формат "25.01" или подобные
            parts = re.findall(r'\d+', date_str)
            if len(parts) >= 2:
                day = int(parts[0])
                month = int(parts[1])
                year = datetime.now().year
                # TODO: Добавить логику смены года, если загрузка в следующем году
                return datetime(year, month, day).date()
        except Exception:
            pass
        return None

    def _parse_cargo_info(self, info: str) -> Tuple[float, str]:
        """
        Парсит строку вида '24 t, Tarp' или '1500 kg, Box'.
        Возвращает (вес в кг, тип кузова).
        """
        weight = 0.0
        body = ""
        if not info: return weight, body
        
        # Извлекаем вес
        weight_match = re.search(r'(\d+[.,]?\d*)\s*(t|kg|т|кг)', info.lower())
        if weight_match:
            val_str = weight_match.group(1).replace(',', '.')
            unit = weight_match.group(2)
            try:
                val = float(val_str)
                if unit in ['t', 'т']:
                    weight = val * 1000
                else:
                    weight = val
            except ValueError:
                pass
        
        # Извлекаем тип кузова (после запятой или остаток)
        if ',' in info:
            body = info.split(',')[-1].strip()
        else:
            # Если запятой нет, попробуем убрать вес из начала
            body = re.sub(r'^\d+[.,]?\d*\s*(t|kg|т|кг)\s*', '', info, flags=re.IGNORECASE).strip()
            
        return weight, body

    def _parse_price(self, price_str: str) -> Optional[float]:
        if not price_str: return None
        # Оставляем цифры и разделители
        clean = re.sub(r'[^\d.,]', '', price_str).replace(',', '.')
        try:
            return float(clean)
        except ValueError:
            return None

    def _parse_int(self, val_str: str) -> Optional[int]:
        if not val_str: return None
        clean = re.sub(r'[^\d]', '', val_str)
        try:
            return int(clean)
        except ValueError:
            return None
