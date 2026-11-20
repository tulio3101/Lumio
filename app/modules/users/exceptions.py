from fastapi import status

from app.core.errors import AppError


class AccountDeletionError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "account_deletion_failed"
    message = "No se pudo eliminar la cuenta. Tu cuenta sigue activa; intenta de nuevo."
