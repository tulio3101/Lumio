from fastapi import status

from app.core.errors import AppError
from app.modules.contacts.models import MAX_CONTACTS_PER_USER


class ContactNotFoundError(AppError):
    # También cuando el contacto es de otro usuario: no se revela que existe.
    status_code = status.HTTP_404_NOT_FOUND
    code = "contact_not_found"
    message = "No se encontró ese contacto. Puede que ya lo hayas eliminado."


class ContactDuplicateError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "contact_duplicate"
    message = "Ya tienes un contacto con ese correo."


class ContactLimitReachedError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "contact_limit_reached"
    message = (
        f"Ya tienes {MAX_CONTACTS_PER_USER} contactos de confianza, que es el máximo. "
        "Elimina uno para agregar otro."
    )


class ContactIsOwnEmailError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "contact_is_own_email"
    message = "Ese es tu propio correo. Escribe el de otra persona."


class ContactSaveError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "contact_save_failed"
    message = "No se pudo guardar el contacto. Tus contactos siguen como estaban; intenta de nuevo."


class ContactDeleteError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "contact_delete_failed"
    message = "No se pudo eliminar el contacto. Sigue en tu lista; intenta de nuevo."
