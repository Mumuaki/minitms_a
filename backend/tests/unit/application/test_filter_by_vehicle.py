"""
Unit tests for FilterByVehicleUseCase.
"""

import pytest
from datetime import date
from unittest.mock import Mock

from backend.src.application.use_cases.cargo.filter_by_vehicle import FilterByVehicleUseCase
from backend.src.application.dto.cargo_dto import (
    SearchCargoRequestDto,
    SearchCargoResponseDto,
    CargoDto,
    LocationDto,
    ProfitabilityDto,
    CargoStatusColor
)


class TestFilterByVehicleUseCase:
    """Test cases for FilterByVehicleUseCase."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_repo = Mock()
        self.mock_profitability_calculator = Mock()
        self.use_case = FilterByVehicleUseCase(self.mock_repo, self.mock_profitability_calculator)

    def test_execute_success(self):
        """Test successful execution of filtering."""
        # Arrange
        expected_response = SearchCargoResponseDto(
            items=[],
            total=0,
            page=1,
            limit=10,
            total_pages=0
        )

        self.mock_repo.search_cargos.return_value = expected_response

        # Act
        result = self.use_case.execute(
            vehicle_body_type="TENT",
            vehicle_max_weight=20.0,
            page=1,
            limit=10
        )

        # Assert
        assert result == expected_response
        # Verify that search_cargos was called with correct parameters
        call_args = self.mock_repo.search_cargos.call_args[0][0]
        assert call_args.vehicle_body_type == "TENT"
        assert call_args.vehicle_max_weight == 20.0

    def test_execute_with_all_vehicle_params(self):
        """Test execution with all vehicle parameters."""
        # Arrange
        expected_response = SearchCargoResponseDto(
            items=[],
            total=0,
            page=1,
            limit=10,
            total_pages=0
        )

        self.mock_repo.search_cargos.return_value = expected_response

        # Act
        result = self.use_case.execute(
            vehicle_body_type="FRIGO",
            vehicle_max_weight=15.0,
            vehicle_capacity=50.0,
            vehicle_length=12.0,
            vehicle_width=2.5,
            vehicle_height=2.8,
            page=1,
            limit=10
        )

        # Assert
        assert result == expected_response
        call_args = self.mock_repo.search_cargos.call_args[0][0]
        assert call_args.vehicle_body_type == "FRIGO"
        assert call_args.vehicle_max_weight == 15.0
        assert call_args.vehicle_capacity == 50.0
        assert call_args.vehicle_length == 12.0
        assert call_args.vehicle_width == 2.5
        assert call_args.vehicle_height == 2.8

    def test_execute_with_profitability_calculation(self):
        """Test execution with profitability calculation."""
        # Arrange
        cargo_item = CargoDto(
            id="1",
            external_id="ext1",
            source="trans.eu",
            loading_place=LocationDto(address="Loading", country_code="DE", lat=52.52, lon=13.405),
            unloading_place=LocationDto(address="Unloading", country_code="FR", lat=48.8566, lon=2.3522),
            price=1000.0,
            distance_trans_eu=500,
            distance_osm=520,
            is_hidden=False,
            created_at="2026-01-01T00:00:00"
        )

        expected_response = SearchCargoResponseDto(
            items=[cargo_item],
            total=1,
            page=1,
            limit=10,
            total_pages=1
        )

        self.mock_repo.search_cargos.return_value = expected_response

        # Mock profitability calculator
        from backend.src.domain.value_objects.profitability import Profitability, ProfitabilityStatus
        mock_profitability = Profitability(
            rate_per_km=1.5,
            total_cost=500.0,
            empty_run_km=50.0,
            total_distance=550.0,
            status_color=ProfitabilityStatus.GREEN
        )
        self.mock_profitability_calculator.calculate.return_value = mock_profitability

        # Act
        result = self.use_case.execute(
            vehicle_body_type="TENT",
            fuel_consumption=25.0,
            fuel_price=1.2,
            depreciation_per_km=0.5,
            driver_salary_per_km=0.3,
            other_costs_per_km=0.2,
            empty_run_distance=50.0,
            distance_type="trans_eu",
            page=1,
            limit=10
        )

        # Assert
        assert result.items[0].profitability is not None
        assert result.items[0].profitability.rate_per_km == 1.5
        assert result.items[0].profitability.empty_run_km == 50.0
        assert result.items[0].profitability.total_distance == 550.0
        assert result.items[0].profitability.color_code == "GREEN"
        self.mock_profitability_calculator.calculate.assert_called_once()

    def test_validate_request_invalid_vehicle_max_weight(self):
        """Test validation of invalid vehicle_max_weight."""
        # Act & Assert
        with pytest.raises(ValueError, match="vehicle_max_weight cannot be negative"):
            self.use_case.execute(vehicle_max_weight=-5.0)

    def test_validate_request_invalid_vehicle_capacity(self):
        """Test validation of invalid vehicle_capacity."""
        # Act & Assert
        with pytest.raises(ValueError, match="vehicle_capacity cannot be negative"):
            self.use_case.execute(vehicle_capacity=-10.0)

    def test_validate_request_invalid_vehicle_length(self):
        """Test validation of invalid vehicle_length."""
        # Act & Assert
        with pytest.raises(ValueError, match="vehicle_length cannot be negative"):
            self.use_case.execute(vehicle_length=-2.0)

    def test_validate_request_invalid_vehicle_width(self):
        """Test validation of invalid vehicle_width."""
        # Act & Assert
        with pytest.raises(ValueError, match="vehicle_width cannot be negative"):
            self.use_case.execute(vehicle_width=-1.5)

    def test_validate_request_invalid_vehicle_height(self):
        """Test validation of invalid vehicle_height."""
        # Act & Assert
        with pytest.raises(ValueError, match="vehicle_height cannot be negative"):
            self.use_case.execute(vehicle_height=-3.0)