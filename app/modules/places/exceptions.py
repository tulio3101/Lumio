from fastapi import status

from app.core.errors import AppError


class ActiveRouteNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "active_route_not_found"
    message = "No hay una ruta activa."


class ActiveRouteConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "active_route_conflict"
    message = "La ruta activa cambió mientras se guardaba. Intenta de nuevo."
