from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ErrorResponse
from app.modules.places.repository import RouteRepository
from app.modules.places.schemas import (
    ActiveRoute,
    ActiveRouteUpdate,
    RouteCreate,
    RouteHistoryPage,
)
from app.modules.places.service import RouteService
from app.modules.users.dependencies import CurrentUserId

router = APIRouter(prefix="/places", tags=["places"])

NOT_IMPLEMENTED = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="No implementado"
)

_UNAUTHORIZED: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Usuario no identificado.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "Persistencia no disponible.",
    },
}


def get_route_service(db: Annotated[Session, Depends(get_db)]) -> RouteService:
    return RouteService(RouteRepository(db))


RouteServiceDep = Annotated[RouteService, Depends(get_route_service)]


@router.put(
    "/routes/active",
    response_model=ActiveRoute,
    summary="Iniciar o reemplazar la ruta activa",
    description=(
        "Guarda una ruta peatonal ya calculada en el dispositivo como la ruta activa del "
        "usuario. Si había una ruta activa o pausada, queda cancelada."
    ),
    responses={
        **_UNAUTHORIZED,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Otra petición cambió la ruta activa al mismo tiempo.",
        },
    },
)
def start_active_route(
    payload: RouteCreate, user_id: CurrentUserId, service: RouteServiceDep
) -> ActiveRoute:
    return ActiveRoute.model_validate(service.start_active_route(user_id, payload))


@router.get(
    "/routes/active",
    response_model=ActiveRoute,
    summary="Estado de la ruta activa",
    responses={
        **_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "No hay ruta activa."},
    },
)
def get_active_route(user_id: CurrentUserId, service: RouteServiceDep) -> ActiveRoute:
    return ActiveRoute.model_validate(service.get_active_route(user_id))


@router.patch(
    "/routes/active",
    response_model=ActiveRoute,
    summary="Actualizar progreso o estado de la ruta activa",
)
def update_active_route(payload: ActiveRouteUpdate) -> ActiveRoute:
    raise NOT_IMPLEMENTED


@router.delete(
    "/routes/active", status_code=status.HTTP_204_NO_CONTENT, summary="Cancelar la ruta activa"
)
def cancel_active_route() -> None:
    raise NOT_IMPLEMENTED


@router.get("/routes/history", response_model=RouteHistoryPage, summary="Historial de rutas")
def list_route_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> RouteHistoryPage:
    raise NOT_IMPLEMENTED
