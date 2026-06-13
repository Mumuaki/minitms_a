from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class TransEuScraperPort(ABC):
    """
    Абстракция над модулем парсинга Trans.eu (Secondary/Driven Port).
    """

    @abstractmethod
    async def login(self) -> bool:
        """
        Вход в систему (инициализация сессии).
        """
        pass

    @abstractmethod
    async def fetch_offers(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Получение сырых данных предложений (парсинг или API).
        
        Args:
            criteria: Параметры поиска (loading_location, unloading_location, radius и т.д.)
            
        Returns:
            Список сырых данных предложений (RawOfferData) в виде словарей.
        """
        pass