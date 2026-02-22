"""
Import Trans.eu Offers Use Case.
Orchestrates the scraping, normalization, and persistence of cargo offers.
"""

from typing import List, Optional
import logging

from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.infrastructure.external_services.trans_eu.client import TransEuClient
from backend.src.application.dto.cargo_dto import CargoDto, LocationDto, CargoStatusColor
from backend.src.application.use_cases.cargo.calculate_profitability import CalculateProfitabilityUseCase

logger = logging.getLogger(__name__)

class ImportTransEuOffersUseCase:
    
    def __init__(self, 
                 cargo_repository: CargoRepository, 
                 # vehicle_repository (future optimization for profitability)
                 ):
        self.cargo_repository = cargo_repository
        # We assume client is instantiated per request or injected. 
        # For this use case, we'll instantiate it here or pass it in execute.
        # But Client is stateful.
        self._profitability_calculator = CalculateProfitabilityUseCase() 

    async def execute(self, 
                      loading: str, 
                      unloading: str,
                      loading_radius: int = 75,
                      unloading_radius: int = 75,
                      date_from: str = None,
                      date_to: str = None,
                      unloading_date_from: str = None,
                      unloading_date_to: str = None,
                      weight_to: str = "0.9",
                      length_to: str = None
                      ) -> List[CargoDto]:
        
        """
        Executes the scraping process and saves results to DB.
        """
        client = TransEuClient()
        try:
            # 1. Start & Login
            await client.start()
            if not await client.login():
                raise Exception("Failed to login to Trans.eu")
            
            # 2. Search
            results_list = await client.search_offers(
                loading_location=loading,
                unloading_location=unloading,
                loading_radius=loading_radius,
                unloading_radius=unloading_radius,
                date_from=date_from,
                date_to=date_to,
                unloading_date_from=unloading_date_from,
                unloading_date_to=unloading_date_to,
                weight_to=weight_to,
                length_to=length_to
            )
            
            # 3. Persist
            saved_cargos = []
            if results_list:
                for item in results_list:
                    try:
                        dto = self._map_dict_to_dto(item)
                        
                        # Upsert logic
                        existing = self.cargo_repository.get_by_external_id(dto.external_id)
                        if existing:
                            # Update fields
                            dto.id = existing.id # Preserve internal ID
                            saved = self.cargo_repository.update(dto)
                        else:
                            saved = self.cargo_repository.create(dto)
                        
                        saved_cargos.append(saved)
                    except Exception as e:
                        logger.error(f"Failed to save cargo {item.get('external_id')}: {e}")
            
            return saved_cargos
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise e
        finally:
            # IMPORTANT: As per previous instruction, we might NOT want to close the browser
            # if the session is to be kept alive. However, for an API request, response time matters.
            # But the user said "only user can close session". 
            # So we do NOT call client.stop().
            # BUT, client.stop() kills the playwright process. 
            pass

    def _map_dict_to_dto(self, item: dict) -> CargoDto:
        """
        Convert mapper dictionary to CargoDto.
        """
        # Create minimal LocationDto (Geocoding to be added later or separated)
        loading_loc = LocationDto(
            address=item.get("loading_place", {}).get("raw") or "Unknown",
            country_code="EU", # Placeholder
            lat=0.0,
            lon=0.0
        )
        unloading_loc = LocationDto(
            address=item.get("unloading_place", {}).get("raw") or "Unknown",
            country_code="EU",
            lat=0.0,
            lon=0.0
        )

        # Dates - parse if possible, or leave None
        # item['loading_date_raw'] might be "28.01"
        # We need a robust date parser here or in mapper. 
        # For now, let's keep it None if mapper didn't produce date objects.
        # Mapper currently returns raw strings mostly.
        
        dto = CargoDto(
            id="", # Will be assigned by DB or ignored on create
            external_id=item.get("external_id") or f"gen-{item.get('company_name')}-{item.get('price')}", # Fallback/Mock
            source="trans.eu",
            loading_place=loading_loc,
            unloading_place=unloading_loc,
            loading_date=None, # To be implemented: string to date parsing
            unloading_date=None,
            weight=item.get("weight"), # Float
            body_type=item.get("body_type"),
            price=item.get("price"),
            distance_trans_eu=item.get("distance_trans_eu"),
            distance_osm=None,
            profitability=None,
            is_hidden=False,
            created_at="" # Pydantic/Orm will handle
        )
        
        return dto
