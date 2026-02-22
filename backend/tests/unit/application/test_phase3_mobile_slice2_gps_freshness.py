from importlib import import_module
import inspect
from unittest.mock import Mock

import pytest


@pytest.mark.requirement_id("FR-FLEET-002")
@pytest.mark.test_id("TST-FR-FLEET-002-MOB-AT-S2")
def test_fr_fleet_002_mobile_fleet_map_use_case_contract_exists():
    module = import_module("backend.src.application.use_cases.mobile.get_mobile_fleet_map")
    use_case = getattr(module, "GetMobileFleetMapUseCase")
    assert inspect.isclass(use_case)
    assert hasattr(use_case, "execute")

    result_model = getattr(module, "MobileFleetPosition")
    assert inspect.isclass(result_model)
    assert "freshness_seconds" in result_model.__annotations__


@pytest.mark.requirement_id("FR-FLEET-002")
@pytest.mark.test_id("TST-FR-FLEET-002-MOB-INTEG-S2")
def test_fr_fleet_002_fleet_map_depends_on_gps_position_provider_port():
    module = import_module("backend.src.application.use_cases.mobile.get_mobile_fleet_map")
    use_case = getattr(module, "GetMobileFleetMapUseCase")
    init_signature = inspect.signature(use_case.__init__)
    init_params = set(init_signature.parameters.keys())
    assert "gps_position_provider_port" in init_params


@pytest.mark.requirement_id("FR-FLEET-002")
@pytest.mark.test_id("TST-FR-FLEET-002-MOB-INTEG-S2-INVALID-DATA")
def test_fr_fleet_002_fleet_map_handles_invalid_provider_values():
    module = import_module("backend.src.application.use_cases.mobile.get_mobile_fleet_map")
    use_case_cls = getattr(module, "GetMobileFleetMapUseCase")

    gps_provider = Mock()
    gps_provider.get_positions.return_value = [
        {"vehicle_id": "V-1", "latitude": None, "longitude": "bad", "freshness_seconds": "oops"}
    ]

    use_case = use_case_cls(gps_position_provider_port=gps_provider)
    result = use_case.execute()

    assert len(result) == 1
    assert result[0].latitude == 0.0
    assert result[0].longitude == 0.0
    assert result[0].freshness_seconds == 0
