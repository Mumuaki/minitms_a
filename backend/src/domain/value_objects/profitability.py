"""
Value Object: Profitability

Представляет расчет рентабельности перевозки.
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum


class ProfitabilityStatus(str, Enum):
    """Статус рентабельности по цветовой кодировке."""
    RED = "RED"       # < 0.54 €/км
    GRAY = "GRAY"     # 0.54 - 0.59 €/км
    YELLOW = "YELLOW" # 0.60 - 0.79 €/км
    GREEN = "GREEN"   # ≥ 0.80 €/км


@dataclass(frozen=True)
class Profitability:
    """
    Value Object для рентабельности перевозки.

    Содержит расчетные показатели рентабельности.
    """
    rate_per_km: Optional[float]  # Доход на км (€/км)
    total_cost: Optional[float]    # Общие затраты (€)
    empty_run_km: Optional[float]  # Км порожнего пробега
    total_distance: Optional[float]  # Общее расстояние (км)
    status_color: ProfitabilityStatus  # Цветовой статус

    @property
    def profit_margin(self) -> Optional[float]:
        """Маржа прибыли = (доход - затраты) / доход * 100%."""
        if self.rate_per_km is None or self.total_distance is None or self.total_cost is None:
            return None
        revenue = self.rate_per_km * self.total_distance
        if revenue == 0:
            return None
        return ((revenue - self.total_cost) / revenue) * 100

    @property
    def is_profitable(self) -> bool:
        """Является ли перевозка прибыльной."""
        return self.profit_margin is not None and self.profit_margin > 0

    @classmethod
    def calculate_status_color(cls, rate_per_km: Optional[float]) -> ProfitabilityStatus:
        """Определяет цветовой статус на основе ставки за км."""
        if rate_per_km is None:
            return ProfitabilityStatus.GRAY

        if rate_per_km < 0.54:
            return ProfitabilityStatus.RED
        elif 0.54 <= rate_per_km < 0.60:
            return ProfitabilityStatus.GRAY
        elif 0.60 <= rate_per_km < 0.80:
            return ProfitabilityStatus.YELLOW
        else:
            return ProfitabilityStatus.GREEN