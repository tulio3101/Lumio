from fastapi import APIRouter, HTTPException, status

from app.core.db import DbSession
from app.modules.users import service
from app.modules.users.schemas import (
    GoogleAuthRequest,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserLogin,
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


@router.post("/refresh", response_model=TokenPair, summary="Renovar tokens")
def refresh(payload: RefreshRequest) -> TokenPair:
    raise NOT_IMPLEMENTED


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
def logout(payload: RefreshRequest) -> None:
    raise NOT_IMPLEMENTED


@router.get("/me", response_model=UserRead, summary="Usuario autenticado")
def me() -> UserRead:
    raise NOT_IMPLEMENTED
