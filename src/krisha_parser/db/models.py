"""Database models"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Apartment:
    """Apartment model"""
    krisha_id: str  # Unique ID from krisha.kz
    jk_name: str | None  # Complex/building name
    district: str
    address: str
    price: int
    area: float
    rooms: int
    price_per_sqm: float
    description: str | None
    photos_count: int
    phone: str | None
    seller_type: str  # owner/agency/realtor
    url: str
    parsed_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class JKMetrics:
    """Aggregated metrics for a residential complex (ЖК)"""
    jk_name: str
    district: str
    avg_price: float
    avg_price_per_sqm: float
    avg_area: float
    median_price: float
    count_total: int
    count_1room: int
    count_2room: int
    count_3plus_room: int
    min_price: int
    max_price: int
    snapshot_date: str
