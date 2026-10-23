import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RouteStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Place(BaseModel):
    name: str = Field(examples=["Farmacia Central"])
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RouteStep(BaseModel):
    order: int = Field(ge=0)
    instruction: str = Field(description="Instrucción lista para narrar.")
    distance_meters: float = Field(ge=0)


class RouteCreate(BaseModel):
    origin: Place
    destination: Place
    steps: list[RouteStep] = Field(default_factory=list)


class ActiveRouteUpdate(BaseModel):
    status: RouteStatus | None = None
    current_step: int | None = Field(default=None, ge=0)


class ActiveRoute(BaseModel):
    id: uuid.UUID
    origin: Place
    destination: Place
    steps: list[RouteStep]
    current_step: int = Field(ge=0)
    status: RouteStatus
    started_at: datetime


class RouteHistoryItem(BaseModel):
    id: uuid.UUID
    origin: Place
    destination: Place
    status: RouteStatus
    started_at: datetime
    finished_at: datetime | None = None


class RouteHistoryPage(BaseModel):
    items: list[RouteHistoryItem]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
