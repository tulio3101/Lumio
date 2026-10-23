from fastapi import APIRouter, HTTPException, Query, status

from app.modules.places.schemas import (
    ActiveRoute,
    ActiveRouteUpdate,
    RouteCreate,
    RouteHistoryPage,
)

router = APIRouter(prefix="/places", tags=["places"])

NOT_IMPLEMENTED = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="No implementado"
)


@router.put(
    "/routes/active", response_model=ActiveRoute, summary="Iniciar o reemplazar la ruta activa"
)
def start_active_route(payload: RouteCreate) -> ActiveRoute:
    raise NOT_IMPLEMENTED


@router.get("/routes/active", response_model=ActiveRoute, summary="Estado de la ruta activa")
def get_active_route() -> ActiveRoute:
    raise NOT_IMPLEMENTED


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
