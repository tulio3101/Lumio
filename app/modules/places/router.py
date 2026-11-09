import uuid
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
    RouteDestinationChange,
    RouteHistoryItem,
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
        "description": "Falta el access token o la sesión no es válida.",
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


@router.put(
    "/routes/{route_id}/destination",
    response_model=ActiveRoute,
    summary="Cambiar el destino de una ruta abierta",
    description=(
        "Sustituye el recorrido de la ruta (origen, destino, pasos, distancia y duración) "
        "por uno nuevo calculado en el dispositivo desde la ubicación actual. La ruta "
        "conserva su id, vuelve al primer paso y queda activa."
    ),
    responses={
        **_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "La ruta no existe o es de otro usuario.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "La ruta ya terminó o se canceló.",
        },
    },
)
def change_route_destination(
    route_id: uuid.UUID,
    payload: RouteDestinationChange,
    user_id: CurrentUserId,
    service: RouteServiceDep,
) -> ActiveRoute:
    return ActiveRoute.model_validate(service.change_destination(user_id, route_id, payload))


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


@router.get(
    "/routes/history",
    response_model=RouteHistoryPage,
    summary="Historial de rutas",
    description=(
        "Rutas completadas o canceladas del usuario, de la más reciente a la más antigua "
        "según la fecha en que terminaron. La ruta activa o pausada no aparece. Una ruta "
        "queda cancelada cuando se inicia otra."
    ),
    responses={**_UNAUTHORIZED},
)
def list_route_history(
    user_id: CurrentUserId,
    service: RouteServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RouteHistoryPage:
    routes, total = service.list_history(user_id, limit=limit, offset=offset)
    return RouteHistoryPage(
        items=[RouteHistoryItem.model_validate(route) for route in routes],
        total=total,
        limit=limit,
        offset=offset,
    )
