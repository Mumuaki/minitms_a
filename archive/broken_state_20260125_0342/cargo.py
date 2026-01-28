"""
Domain Entity: Cargo

Сущность груза (предложения), полученного из внешних систем (например, Trans.eu).
"""

import enum
import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any

from sqlalchemy import String, Boolean, Integer, DateTime, Date, Numeric, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from backend.src.domain.entities.user import Base


class CargoStatusColor(enum.Enum):
    """Цветовая кодировка рентабельности согласно BR-010 - BR-013."""
    RED = "RED"       # < 0.54 €/км
    GRAY = "GRAY"     # 0.54 - 0.59 €/км
    YELLOW = "YELLOW" # 0.60 - 0.79 €/км
    GREEN = "GREEN"   # ≥ 0.80 €/км


class Cargo(Base):
    """
    Сущность Cargo (Найденный груз / OffersNormalized).
    
    Соответствует разделу 2.4 spec_entities.md.
    """
    
    __tablename__ = "cargos"

    # Идентификатор в нашей системе
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # Идентификатор на внешней платформе (Trans.eu ID)
    external_id: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True
    )
    
    # Источник данных
    source: Mapped[str] = mapped_column(String(50), default="trans.eu")
    
    # Место загрузки (City, Zip, Country, Coordinates)
    loading_place: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Место выгрузки (City, Zip, Country, Coordinates)
    unloading_place: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Даты
    loading_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    unloading_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Характеристики груза
    weight: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    body_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Финансовые показатели
    price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Дистанции
    distance_trans_eu: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    distance_osm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Рентабельность
    rate_per_km: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Статус рентабельности
    status_color: Mapped[CargoStatusColor] = mapped_column(
        SQLEnum(CargoStatusColor, native_enum=False),
        default=CargoStatusColor.GRAY,
        nullable=False
    )
    
    # Служебные флаги
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Таймстампы
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<Cargo(id={self.id}, ext_id='{self.external_id}', price={self.price})>"
