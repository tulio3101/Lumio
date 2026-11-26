from fastapi import status

from app.core.errors import AppError


class ActiveRouteNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "active_route_not_found"
    message = "No hay una ruta activa."


class RouteNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "route_not_found"
    message = "No existe esa ruta."


class RouteNotOpenError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "route_not_open"
    message = "La ruta ya terminó o se canceló; no se puede cambiar su destino."


class RouteNotOpenForRerouteError(RouteNotOpenError):
    message = "La ruta ya terminó o se canceló; no se puede recalcular."


class RouteDestinationMismatchError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "route_destination_mismatch"
    message = (
        "El recorrido recalculado va hacia otro destino. Para cambiar el destino usa "
        "PUT /places/routes/{route_id}/destination."
    )


class RouteIdConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "route_id_conflict"
    message = "Ya existe una ruta con ese id."


class ActiveRouteConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "active_route_conflict"
    message = "La ruta activa cambió mientras se guardaba. Intenta de nuevo."
