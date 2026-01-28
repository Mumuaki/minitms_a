"""
Unit tests for SearchCargosUseCase.
"""

import pytest
from datetime import date
from unittest.mock import Mock

from backend.src.application.use_cases.cargo.search_cargos import SearchCargosUseCase
from backend.src.application.dto.cargo_dto import (
    SearchCargoRequestDto,
    SearchCargoResponseDto,
    CargoDto,
    LocationDto,
    ProfitabilityDto,
    CargoStatusColor
)


class TestSearchCargosUseCase:
    """Test cases for SearchCargosUseCase."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_repo = Mock()
        self.mock_profitability_calculator = Mock()
        self.use_case = SearchCargosUseCase(self.mock_repo, self.mock_profitability_calculator)

    def test_execute_success(self):
        """Test successful execution of search."""
        # Arrange
        request = SearchCargoRequestDto(
            page=1,
            limit=10,
            order_by="created_at",
            order_direction="desc"
        )

        expected_response = SearchCargoResponseDto(
            items=[],
            total=0,
            page=1,
            limit=10,
            total_pages=0
        )

        self.mock_repo.search_cargos.return_value = expected_response

        # Act
        result = self.use_case.execute(request)

        # Assert
        assert result == expected_response
        self.mock_repo.search_cargos.assert_called_once_with(request)

    def test_execute_with_filters(self):
        """Test execution with various filters."""
        # Arrange
        request = SearchCargoRequestDto(
            loading_date_from=date(2026, 1, 1),
            loading_date_to=date(2026, 1, 31),
            weight_min=1.0,
            weight_max=10.0,
            body_type="TENT",
            price_min=100.0,
            price_max=1000.0,
            status_colors=[CargoStatusColor.GREEN],
            source="trans.eu",
            is_hidden=False,
            order_by="price",
            order_direction="asc",
            page=1,
            limit=20
        )

        expected_response = SearchCargoResponseDto(
            items=[],
            total=0,
            page=1,
            limit=20,
            total_pages=0
        )

        self.mock_repo.search_cargos.return_value = expected_response

        # Act
        result = self.use_case.execute(request)

        # Assert
        assert result == expected_response
        self.mock_repo.search_cargos.assert_called_once_with(request)

    def test_execute_with_profitability_calculation(self):
        """Test execution with profitability calculation."""
        # Arrange
        request = SearchCargoRequestDto(
            fuel_consumption=25.0,
            fuel_price=1.2,
            depreciation_per_km=0.5,
            driver_salary_per_km=0.3,
            other_costs_per_km=0.2,
            empty_run_distance=50.0,
            distance_type="trans_eu",
            page=1,
            limit=10,
            order_by="created_at",
            order_direction="desc"
        )

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
        result = self.use_case.execute(request)

        # Assert
        assert result.items[0].profitability is not None
        assert result.items[0].profitability.rate_per_km == 1.5
        assert result.items[0].profitability.empty_run_km == 50.0
        assert result.items[0].profitability.total_distance == 550.0
        assert result.items[0].profitability.color_code == "GREEN"
        self.mock_profitability_calculator.calculate.assert_called_once()

    def test_validate_request_invalid_date_range(self):
        """Test validation of invalid date ranges."""
        # Arrange
        request = SearchCargoRequestDto(
            loading_date_from=date(2026, 1, 31),
            loading_date_to=date(2026, 1, 1),  # Earlier than from
            page=1,
            limit=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="loading_date_from cannot be after loading_date_to"):
            self.use_case.execute(request)

    def test_validate_request_invalid_weight_range(self):
        """Test validation of invalid weight ranges."""
        # Arrange
        request = SearchCargoRequestDto(
            weight_min=10.0,
            weight_max=5.0,  # Min > Max
            page=1,
            limit=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="weight_min cannot be greater than weight_max"):
            self.use_case.execute(request)

    def test_validate_request_invalid_price_range(self):
        """Test validation of invalid price ranges."""
        # Arrange
        request = SearchCargoRequestDto(
            price_min=1000.0,
            price_max=100.0,  # Min > Max
            page=1,
            limit=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="price_min cannot be greater than price_max"):
            self.use_case.execute(request)

    def test_validate_request_invalid_distance_range(self):
        """Test validation of invalid distance ranges."""
        # Arrange
        request = SearchCargoRequestDto(
            distance_min=1000,
            distance_max=500,  # Min > Max
            page=1,
            limit=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="distance_min cannot be greater than distance_max"):
            self.use_case.execute(request)

    def test_validate_request_invalid_distance_type(self):
        """Test validation of invalid distance type."""
        # Arrange
        request = SearchCargoRequestDto(
            distance_type="invalid",
            page=1,
            limit=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="distance_type must be 'trans_eu' or 'osm'"):
            self.use_case.execute(request)

    def test_validate_request_invalid_order_direction(self):
        """Test validation of invalid order direction."""
        # Arrange
        request = SearchCargoRequestDto(
            order_direction="invalid",
            page=1,
            limit=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="order_direction must be 'asc' or 'desc'"):
            self.use_case.execute(request)

    def test_validate_request_invalid_order_by(self):
        """Test validation of invalid order by field."""
        # Arrange
        request = SearchCargoRequestDto(
            order_by="invalid_field",
            page=1,
            limit=10
        )

        # Act & Assert
        with pytest.raises(ValueError, match="order_by must be one of"):
            self.use_case.execute(request)