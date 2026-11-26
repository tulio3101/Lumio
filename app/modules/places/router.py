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
    FinishedRouteCreate,
    RouteCreate,
    RouteDestinationChange,
    RouteFinish,
    RouteHistoryItem,
    RouteHistoryPage,
    RouteReroute,
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


@router.put(
    "/routes/{route_id}/reroute",
    response_model=ActiveRoute,
    summary="Recalcular el recorrido de una ruta abierta",
    description=(
        "Sustituye el recorrido (origen, pasos, distancia y duración) por uno recalculado en "
        "el dispositivo desde la ubicación actual, cuando el usuario se desvió. El destino "
        "debe ser el mismo de la ruta. La ruta conserva su id, vuelve al primer paso, queda "
        "activa y suma un recálculo (`reroute_count`, `last_rerouted_at`)."
    ),
    responses={
        **_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "La ruta no existe o es de otro usuario.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "La ruta ya terminó o se canceló (`route_not_open`), o el destino no es el "
                "de la ruta (`route_destination_mismatch`)."
            ),
        },
    },
)
def reroute_route(
    route_id: uuid.UUID,
    payload: RouteReroute,
    user_id: CurrentUserId,
    service: RouteServiceDep,
) -> ActiveRoute:
    return ActiveRoute.model_validate(service.reroute(user_id, route_id, payload))


@router.post(
    "/routes/{route_id}/finish",
    response_model=RouteHistoryItem,
    summary="Finalizar una ruta",
    description=(
        "Cierra una ruta abierta como `completed` (se llegó al destino) o `cancelled` "
        "(se terminó sin llegar) con la hora de fin del dispositivo, y queda en el "
        "historial. Si la ruta ya estaba cerrada se devuelve sin cambios, así que "
        "reintentar es seguro."
    ),
    responses={
        **_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "La ruta no existe o es de otro usuario.",
        },
    },
)
def finish_route(
    route_id: uuid.UUID,
    payload: RouteFinish,
    user_id: CurrentUserId,
    service: RouteServiceDep,
) -> RouteHistoryItem:
    return RouteHistoryItem.model_validate(service.finish_route(user_id, route_id, payload))


@router.post(
    "/routes/history",
    response_model=RouteHistoryItem,
    status_code=status.HTTP_201_CREATED,
    summary="Guardar una ruta ya finalizada",
    description=(
        "Guarda en el historial una ruta finalizada en el dispositivo que nunca llegó al "
        "backend (se usó sin conexión). No toca la ruta activa. Reenviar el mismo `id` "
        "devuelve la ruta ya guardada sin duplicarla."
    ),
    responses={
        **_UNAUTHORIZED,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "El id ya pertenece a una ruta de otro usuario.",
        },
    },
)
def record_finished_route(
    payload: FinishedRouteCreate, user_id: CurrentUserId, service: RouteServiceDep
) -> RouteHistoryItem:
    return RouteHistoryItem.model_validate(service.record_finished_route(user_id, payload))


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
