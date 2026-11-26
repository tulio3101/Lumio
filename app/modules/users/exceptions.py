from fastapi import status

from app.core.errors import AppError


class AccountDeletionError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "account_deletion_failed"
    message = "No se pudo eliminar la cuenta. Tu cuenta sigue activa; intenta de nuevo."


class ProfileUpdateError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "profile_update_failed"
    message = "No se pudieron guardar los cambios. Tus datos siguen como estaban; intenta de nuevo."


class PreferencesUpdateError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "preferences_update_failed"
    message = "No se pudieron guardar las preferencias. Siguen como estaban; intenta de nuevo."


class InvalidCurrentPasswordError(AppError):
    # 403 y no 401: el access token es válido, y un 401 haría que el cliente renueve la sesión.
    status_code = status.HTTP_403_FORBIDDEN
    code = "invalid_current_password"
    message = "La contraseña actual no es correcta."


class PasswordNotSetError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "password_not_set"
    message = "Tu cuenta no tiene contraseña porque usas Google para iniciar sesión."


class PasswordUnchangedError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "password_unchanged"
    message = "La nueva contraseña debe ser distinta de la actual."


class PasswordChangeError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "password_change_failed"
    message = "No se pudo cambiar la contraseña. Sigue siendo la misma; intenta de nuevo."
