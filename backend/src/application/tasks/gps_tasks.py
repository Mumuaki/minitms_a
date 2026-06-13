import logging
from celery import shared_task
from backend.src.infrastructure.messaging.celery_app import celery_app
from backend.src.infrastructure.persistence.sqlalchemy.database import SessionLocal
from backend.src.application.use_cases.fleet.refresh_vehicle_location import RefreshVehicleLocationUseCase

logger = logging.getLogger(__name__)

@celery_app.task(name="sync_daily_mileage")
def sync_daily_mileage():
    """
    Фоновая задача для синхронизации ежедневного пробега автомобилей.
    По спецификации запускается ежедневно в 00:05.
    """
    logger.info("Starting daily mileage sync for all vehicles...")
    
    with SessionLocal() as db:
        try:
            # Получаем все активные ТС через use_case (переиспользуем GetAllVehiclesUseCase)
            from backend.src.application.use_cases.fleet.get_all_vehicles import GetAllVehiclesUseCase
            use_case_get = GetAllVehiclesUseCase(db)
            vehicles = use_case_get.execute()
            
            use_case_refresh = RefreshVehicleLocationUseCase(db)
            
            synced_count = 0
            for v in vehicles:
                if getattr(v, "gps_tracker_id", None):
                    # При вызове refresh location, локация и пробег будут запрошены у провайдера 
                    # и сохранены (в будущем - записаны в PlanExecution как факт)
                    # Сейчас мы просто вызываем обновление локации для актуализации данных
                    updated = use_case_refresh.execute(v.id)
                    if updated:
                        synced_count += 1
                        
            logger.info(f"Daily mileage sync completed successfully. Synced {synced_count} vehicles.")
            return {"status": "ok", "synced": synced_count}
            
        except Exception as e:
            logger.error(f"Error during daily mileage sync: {e}")
            return {"status": "error", "error": str(e)}
