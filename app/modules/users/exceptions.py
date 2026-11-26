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


class InvalidResetCodeError(AppError):
    # Igual para código incorrecto, vencido, agotado o correo sin cuenta: no revela nada.
    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_reset_code"
    message = "El código no es válido o ya venció. Pide uno nuevo."


class PasswordResetError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "password_reset_failed"
    message = "No se pudo completar la recuperación. Tu contraseña sigue igual; intenta de nuevo."


class InvalidCurrentPasswordError(AppError):
    # 403 y no 401: el access token es válido, y un 401 haría que el cliente renueve la sesión.
    status_code = status.HTTP_403_FORBIDDEN
    code = "invalid_current_password"
    message = "La contraseña actual no es correcta."


class PasswordNotSetError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "password_not_set"
    message = "Tu cuenta no tiene contraseña porque usas Google para iniciar sesión."


class InvalidGoogleTokenError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_google_token"
    message = "No se pudo verificar tu cuenta de Google. Intenta de nuevo."


class GoogleEmailNotVerifiedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "google_email_not_verified"
    message = "Tu cuenta de Google no tiene un correo verificado."


class GoogleAccountConflictError(AppError):
    # No se vincula sola: el registro con correo no verifica el correo, así que quien creó
    # esa cuenta pudo no ser el dueño. Se inicia sesión con la contraseña.
    status_code = status.HTTP_409_CONFLICT
    code = "google_account_conflict"
    message = "Ya existe una cuenta con ese correo. Inicia sesión con tu correo y contraseña."


class GoogleAuthUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "google_auth_unavailable"
    message = "El inicio de sesión con Google no está disponible. Intenta más tarde."


class GoogleSignInError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "google_sign_in_failed"
    message = "No se pudo iniciar sesión con Google. Intenta de nuevo."


class PasswordUnchangedError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "password_unchanged"
    message = "La nueva contraseña debe ser distinta de la actual."


class PasswordChangeError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "password_change_failed"
    message = "No se pudo cambiar la contraseña. Sigue siendo la misma; intenta de nuevo."
