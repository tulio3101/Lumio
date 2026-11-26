from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.core.db import DbSession
from app.core.errors import ErrorResponse
from app.modules.sos.email import EmailSenderDep
from app.modules.users import password_reset, service
from app.modules.users.dependencies import CurrentSession, CurrentUser
from app.modules.users.schemas import (
    GoogleAuthRequest,
    PasswordChange,
    PasswordResetAccepted,
    PasswordResetConfirm,
    PasswordResetRequest,
    PreferencesRead,
    PreferencesUpdate,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserProfileUpdate,
    UserRead,
)

router = APIRouter(prefix="/users", tags=["users"])

NOT_IMPLEMENTED = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="No implementado"
)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuenta",
    responses={status.HTTP_409_CONFLICT: {"description": "El correo ya está registrado"}},
)
def register(payload: UserCreate, db: DbSession) -> UserRead:
    try:
        return service.register(db, payload)
    except service.EmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="No se pudo crear la cuenta con ese correo"
        ) from None


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Iniciar sesión con correo y contraseña",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Credenciales incorrectas"}},
)
def login(payload: UserLogin, db: DbSession) -> TokenPair:
    try:
        return service.login(db, payload)
    except service.InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos"
        ) from None


@router.post("/login/google", response_model=TokenPair, summary="Iniciar sesión con Google")
def login_google(payload: GoogleAuthRequest) -> TokenPair:
    raise NOT_IMPLEMENTED


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Renovar tokens",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Refresh token inválido o revocado"}},
)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        return service.refresh(db, payload.refresh_token)
    except service.InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión no válida"
        ) from None


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Refresh token inválido o revocado"}},
)
def logout(payload: RefreshRequest, db: DbSession) -> None:
    try:
        service.logout(db, payload.refresh_token)
    except service.InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión no válida"
        ) from None


@router.post(
    "/password-reset",
    response_model=PasswordResetAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Pedir código para recuperar la contraseña",
    description=(
        "Envía al correo un código de 6 dígitos si es de una cuenta con contraseña propia. "
        "Responde siempre igual, exista o no la cuenta. El código vence a los 15 minutos, "
        "admite 5 intentos y solo vale el último; entre dos pedidos debe pasar un minuto."
    ),
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo procesar (`password_reset_failed`).",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Persistencia no disponible; no se envió nada.",
        },
    },
)
def request_password_reset(
    payload: PasswordResetRequest, db: DbSession, sender: EmailSenderDep
) -> PasswordResetAccepted:
    password_reset.request_reset(db, payload, sender)
    return PasswordResetAccepted()


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Restablecer la contraseña con el código",
    description=(
        "Con el correo, el código y la nueva contraseña (8 a 128 caracteres). Cierra las "
        "sesiones de todos los dispositivos y el código deja de servir. Después se inicia "
        "sesión con la nueva contraseña."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Código incorrecto, vencido o agotado (`invalid_reset_code`).",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo restablecer (`password_reset_failed`); sigue la misma.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Persistencia no disponible; no cambió nada.",
        },
    },
)
def confirm_password_reset(payload: PasswordResetConfirm, db: DbSession) -> None:
    password_reset.confirm_reset(db, payload)


_SESSION_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Falta el access token o la sesión no es válida.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "Persistencia no disponible; no se cambió nada.",
    },
}


@router.get(
    "/me",
    response_model=UserRead,
    summary="Usuario autenticado",
    description="Datos de la cuenta, incluido el perfil configurable (nombre y celular).",
)
def me(user: CurrentUser) -> UserRead:
    return user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Personalizar cuenta",
    description=(
        "Modifica los datos de perfil enviados; los omitidos no cambian y `null` o una "
        "cadena vacía los quita. `display_name`: 1 a 60 caracteres tras recortar espacios, "
        "solo letras, espacios, apóstrofos, puntos y guiones. `phone`: celular colombiano de "
        "10 dígitos que empieza por 3 (se aceptan espacios y guiones, se guarda sin ellos). "
        "El correo no se puede cambiar. Devuelve la cuenta actualizada."
    ),
    responses={
        **_SESSION_ERRORS,
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo guardar (`profile_update_failed`); no cambió nada.",
        },
    },
)
def update_me(payload: UserProfileUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    return service.update_profile(db, user, payload)


@router.get(
    "/me/preferences",
    response_model=PreferencesRead,
    summary="Consultar preferencias de voz y vibración",
    description=(
        "Copia de respaldo de las preferencias del teléfono. Si la cuenta nunca guardó, "
        "devuelve las predeterminadas con `updated_at` null. El teléfono no espera esta "
        "respuesta para aplicar sus preferencias."
    ),
    responses=_SESSION_ERRORS,
)
def get_my_preferences(user: CurrentUser, db: DbSession) -> PreferencesRead:
    return service.get_preferences(db, user)


@router.put(
    "/me/preferences",
    response_model=PreferencesRead,
    summary="Guardar preferencias de voz y vibración",
    description=(
        "Reemplaza todas las preferencias. `voice_language`: variante de español (es-MX, "
        "es-ES, es-419…). `speech_rate`: de 0,5 a 2. `haptic_intensity`: soft, medium o "
        "strong. `haptic_disabled_events`: solo routeReady, routeFailed, routeFinished, "
        "turnLeft y turnRight; las alertas de seguridad no se pueden apagar. Devuelve lo "
        "guardado con `updated_at`."
    ),
    responses={
        **_SESSION_ERRORS,
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo guardar (`preferences_update_failed`); no cambió nada.",
        },
    },
)
def put_my_preferences(
    payload: PreferencesUpdate, user: CurrentUser, db: DbSession
) -> PreferencesRead:
    return service.update_preferences(db, user, payload)


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cambiar contraseña",
    description=(
        "Exige la contraseña actual. La nueva sigue las reglas de registro (8 a 128 "
        "caracteres) y debe ser distinta. Este dispositivo conserva su sesión; las de los "
        "demás se cierran."
    ),
    responses={
        **_SESSION_ERRORS,
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": "La contraseña actual no es correcta (`invalid_current_password`).",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "La cuenta no tiene contraseña: usa Google (`password_not_set`).",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "Nueva contraseña inválida, o igual a la actual (`password_unchanged`)."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo cambiar (`password_change_failed`); sigue la misma.",
        },
    },
)
def change_password(
    payload: PasswordChange, user: CurrentUser, session: CurrentSession, db: DbSession
) -> None:
    service.change_password(db, user, session, payload)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar cuenta",
    description=(
        "Elimina de forma definitiva la cuenta del usuario autenticado y sus datos "
        "asociados: sesiones de todos los dispositivos, ruta activa e historial de rutas, "
        "contactos de confianza, eventos SOS y preferencias. No se puede deshacer. "
        "Después los tokens de la cuenta responden 401 y el inicio de sesión con ese correo "
        "falla; el correo puede registrarse de nuevo como una cuenta nueva."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Falta el access token o la sesión no es válida.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo eliminar (`account_deletion_failed`); la cuenta sigue.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "Persistencia no disponible; la cuenta sigue.",
        },
    },
)
def delete_me(user: CurrentUser, db: DbSession) -> None:
    service.delete_account(db, user)
