import asyncio
import logging
from backend.src.infrastructure.messaging.celery_app import celery_app
from backend.src.infrastructure.persistence.sqlalchemy.database import SessionLocal
from backend.src.infrastructure.persistence.sqlalchemy.repositories.cargo_repository_impl import CargoRepositoryImpl
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from backend.src.infrastructure.external_services.gps.gps_service_impl import GpsServiceImpl
from backend.src.infrastructure.external_services.trans_eu.trans_eu_scraper_adapter import TransEuScraperAdapter
from backend.src.application.use_cases.cargo.scrape_cargos import ScrapeCargoUseCase

from backend.src.infrastructure.utils.retry_utils import RateLimitError

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="backend.src.application.tasks.scraping_tasks.scrape_cargos_task", max_retries=3)
def scrape_cargos_task(self, vehicle_id: str, radius: int = 75, **filters):
    """
    Celery задача для асинхронного запуска скрапинга грузов.
    """
    self.update_state(state='STARTED')
    db = SessionLocal()
    try:
        vehicle_repo = VehicleRepositoryImpl(db)
        cargo_repo = CargoRepositoryImpl(db)
        gps_service = GpsServiceImpl()
        scraper_adapter = TransEuScraperAdapter()
        
        use_case = ScrapeCargoUseCase(
            vehicle_repository=vehicle_repo,
            gps_service=gps_service,
            scraper_port=scraper_adapter,
            cargo_repository=cargo_repo
        )
        
        # Запускаем асинхронный юзкейс в синхронной Celery задаче
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(use_case.execute(vehicle_id, radius, **filters))
        logger.info(f"Scraping task completed for vehicle {vehicle_id}. Saved {len(result)} cargos.")
        return len(result)
    except RateLimitError as e:
        logger.warning(f"RateLimitError (Captcha timeout) for vehicle {vehicle_id}. Retrying later.")
        countdown = 300 * (2 ** self.request.retries)  # 5min, 10min, 20min
        raise self.retry(exc=e, countdown=countdown)
    except Exception as e:
        logger.error(f"Error in scrape_cargos_task for vehicle {vehicle_id}: {e}")
        raise
    finally:
        db.close()
