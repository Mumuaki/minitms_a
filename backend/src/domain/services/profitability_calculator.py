"""
Domain Service: ProfitabilityCalculator

Сервис для расчета рентабельности перевозки.
"""

from typing import Optional
from backend.src.domain.value_objects.profitability import Profitability, ProfitabilityStatus

MIN_DISTANCE_KM = 10.0


class ProfitabilityCalculator:
    """
    Сервис для расчета рентабельности перевозки.

    Использует данные о грузе, транспортном средстве и маршруте.
    """

    def calculate(
        self,
        cargo_price: Optional[float],
        distance: Optional[float],
        empty_run_distance: Optional[float] = 0,
        fuel_consumption: Optional[float] = None,  # л/100км
        fuel_price: Optional[float] = None,        # €/л
        depreciation_per_km: Optional[float] = None,  # €/км
        driver_salary_per_km: Optional[float] = None,  # €/км
        other_costs_per_km: Optional[float] = None     # €/км
    ) -> Profitability:
        """
        Рассчитывает рентабельность перевозки.

        Args:
            cargo_price: Цена груза (€)
            distance: Расстояние груженого пробега (км)
            empty_run_distance: Расстояние порожнего пробега (км)
            fuel_consumption: Расход топлива (л/100км)
            fuel_price: Стоимость топлива (€/л)
            depreciation_per_km: Амортизация (€/км)
            driver_salary_per_km: Зарплата водителя (€/км)
            other_costs_per_km: Прочие расходы (€/км)

        Returns:
            Profitability: Объект с расчетными показателями
        """
        if cargo_price is None or distance is None:
            return Profitability(
                rate_per_km=None,
                total_cost=None,
                empty_run_km=empty_run_distance,
                total_distance=distance,
                status_color=ProfitabilityStatus.GRAY
            )

        total_distance = distance + (empty_run_distance or 0)
        if 0 < total_distance < MIN_DISTANCE_KM:
            total_distance = MIN_DISTANCE_KM

        # Расчет затрат
        total_cost = 0.0

        # Затраты на топливо
        if fuel_consumption is not None and fuel_price is not None:
            fuel_cost = (fuel_consumption / 100) * total_distance * fuel_price
            total_cost += fuel_cost

        # Амортизация
        if depreciation_per_km is not None:
            total_cost += depreciation_per_km * total_distance

        # Зарплата водителя
        if driver_salary_per_km is not None:
            total_cost += driver_salary_per_km * total_distance

        # Прочие расходы
        if other_costs_per_km is not None:
            total_cost += other_costs_per_km * total_distance

        # Расчет ставки за км (рентабельность)
        # rate_per_km = (cargo_price - total_cost) / total_distance
        # Но в модели rate_per_km = cargo_price / distance, видимо
        # Для рентабельности используем (price - cost) / distance
        if total_distance > 0:
            rate_per_km = (cargo_price - total_cost) / total_distance
        else:
            rate_per_km = None

        status_color = Profitability.calculate_status_color(rate_per_km)

        return Profitability(
            rate_per_km=rate_per_km,
            total_cost=total_cost if total_cost > 0 else None,
            empty_run_km=empty_run_distance,
            total_distance=total_distance,
            status_color=status_color
        )
