import uuid
from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_ROUTE_STEPS = 500


class RouteStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class _StrictNumbers(BaseModel):
    # NaN e infinito no son coordenadas ni distancias válidas.
    model_config = ConfigDict(allow_inf_nan=False)


class Place(_StrictNumbers):
    name: str = Field(min_length=1, max_length=200, examples=["Farmacia Central"])
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RouteStep(_StrictNumbers):
    order: int = Field(ge=0)
    instruction: str = Field(
        min_length=1, max_length=500, description="Instrucción lista para narrar."
    )
    distance_meters: float = Field(ge=0, description="Distancia del tramo de este paso.")
    latitude: float | None = Field(
        default=None, ge=-90, le=90, description="Punto donde empieza la maniobra."
    )
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def _coordinates_come_in_pairs(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude y longitude deben enviarse juntas")
        return self


class RouteCreate(_StrictNumbers):
    """Ruta peatonal ya calculada por el cliente (MapKit) que pasa a ser la ruta activa."""

    origin: Place = Field(description="Ubicación actual del usuario al calcular la ruta.")
    destination: Place
    steps: list[RouteStep] = Field(min_length=1, max_length=MAX_ROUTE_STEPS)
    distance_meters: float = Field(gt=0, description="Distancia total de la ruta.")
    expected_travel_time_seconds: float = Field(ge=0, description="Duración estimada a pie.")

    @model_validator(mode="after")
    def _steps_are_sequential(self) -> Self:
        if [step.order for step in self.steps] != list(range(len(self.steps))):
            raise ValueError("steps debe estar ordenado con order consecutivo desde 0")
        return self


class RouteDestinationChange(RouteCreate):
    """Nueva ruta hacia otro destino, calculada en el cliente desde la ubicación actual.

    Sustituye origen, destino, pasos, distancia y duración de la misma ruta; el progreso
    vuelve al primer paso.
    """


class ActiveRouteUpdate(BaseModel):
    status: RouteStatus | None = None
    current_step: int | None = Field(default=None, ge=0)


class ActiveRoute(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    origin: Place
    destination: Place
    steps: list[RouteStep]
    distance_meters: float = Field(ge=0)
    expected_travel_time_seconds: float = Field(ge=0)
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
