"""
Стресс-тест скрапера: 10 запусков с разными параметрами.
"""
import asyncio
import logging
import sys
import os
import random
from datetime import datetime, timedelta

# Utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.src.infrastructure.config.settings import settings
settings.HEADLESS_MODE = False

from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("MultiTest")

CITIES = [
    "SK, Bratislava", "SK, Zilina", "SK, Kosice", "SK, Trnava",
    "PL, Warsaw", "PL, Krakow", "PL, Lodz",
    "DE, Berlin", "DE, Munich", "DE, Hamburg",
    "CZ, Prague", "CZ, Brno",
    "AT, Vienna", "AT, Graz",
    "HU, Budapest"
]

def random_date(start_str, end_str):
    start = datetime.strptime(start_str, "%d.%m.%Y")
    end = datetime.strptime(end_str, "%d.%m.%Y")
    # Корректировка, чтобы не было в прошлом (для client.py валидации)
    now = datetime.now()
    if start < now: start = now
    
    delta = end - start
    if delta.days < 0: return start.strftime("%d.%m.%Y")
    
    random_days = random.randrange(delta.days + 1)
    return (start + timedelta(days=random_days)).strftime("%d.%m.%Y")

async def main():
    client = TransEuClient()
    await client.start()
    
    if not await client.login():
        logger.error("Login failed")
        return

    logger.info(f"Starting 10 variants tests...")

    for i in range(10):
        # Generate random params
        load = random.choice(CITIES)
        unload = random.choice([c for c in CITIES if c != load])
        
        # Load Date: 23.01 - 30.01 (adjusted to >= today)
        d_from = random_date("25.01.2026", "30.01.2026") # Start from today 25
        # Load To is usually same or +2 days
        d_from_dt = datetime.strptime(d_from, "%d.%m.%Y")
        d_to = (d_from_dt + timedelta(days=random.randint(0, 2))).strftime("%d.%m.%Y")
        
        # Unload Date: 25.01 - 28.02 (must be >= load date)
        u_limit = datetime.strptime("28.02.2026", "%d.%m.%Y")
        if u_limit < d_from_dt: u_limit = d_from_dt + timedelta(days=5)
        
        u_from_dt = d_from_dt + timedelta(days=random.randint(1, 5))
        u_to_dt = u_from_dt + timedelta(days=random.randint(0, 3))
        
        u_from = u_from_dt.strftime("%d.%m.%Y")
        u_to = u_to_dt.strftime("%d.%m.%Y")
        
        # Params
        weight = round(random.uniform(0.1, 20.0), 1)
        length = round(random.uniform(1.0, 12.0), 1)
        
        logger.info(f"\n==================================================")
        logger.info(f"TEST {i+1}/10")
        logger.info(f"📍 {load} -> {unload}")
        logger.info(f"📅 Load: {d_from}-{d_to}, Unload: {u_from}-{u_to}")
        logger.info(f"📦 W: {weight}t, L: {length}m")
        logger.info(f"==================================================")
        
        try:
            success = await client.search_offers(
                loading_location=load,
                unloading_location=unload,
                date_from=d_from,
                date_to=d_to,
                unloading_date_from=u_from,
                unloading_date_to=u_to,
                weight_to=str(weight),
                length_to=str(length),
                loading_radius=75,
                unloading_radius=100
            )
            
            if success:
                logger.info(f"✅ Test {i+1} PASSED")
            else:
                logger.error(f"❌ Test {i+1} FAILED")
                
            await asyncio.sleep(3) # Small pause
            
        except Exception as e:
            logger.error(f"❌ Test {i+1} EXCEPTION: {e}")

    logger.info("\nALL TESTS COMPLETED.")
    # Keep open for review
    input("Press Enter to close browser...")
    await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
