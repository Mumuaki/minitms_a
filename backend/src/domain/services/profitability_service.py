from backend.src.application.dto.cargo_dto import ProfitabilityDto, CargoStatusColor

class ProfitabilityService:
    """
    Доменный сервис для расчета рентабельности рейса.
    """
    
    @staticmethod
    def calculate_profitability(price_eur: float, empty_run_km: float, cargo_km: float) -> ProfitabilityDto:
        """
        Расчет рентабельности и цветовой зоны.
        Формула: Цена / (холостой пробег + пробег с грузом)
        """
        total_distance = empty_run_km + cargo_km
        
        if total_distance <= 0:
            # Предотвращение деления на ноль, если координаты не определены
            return ProfitabilityDto(
                rate_per_km=None,
                empty_run_km=empty_run_km,
                total_distance=total_distance,
                color_code=CargoStatusColor.GRAY
            )
            
        rate_per_km = round(price_eur / total_distance, 2)
        
        # Определение цветовой зоны согласно spec_value_objects.md
        if rate_per_km < 0.54:
            color = CargoStatusColor.RED
        elif 0.54 <= rate_per_km <= 0.59:
            color = CargoStatusColor.GRAY
        elif 0.60 <= rate_per_km <= 0.79:
            color = CargoStatusColor.YELLOW
        else: # >= 0.80
            color = CargoStatusColor.GREEN
            
        return ProfitabilityDto(
            rate_per_km=rate_per_km,
            empty_run_km=empty_run_km,
            total_distance=total_distance,
            color_code=color
        )
