from fastapi import APIRouter, HTTPException, status

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
    "", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Crear cuenta"
)
def register(payload: UserCreate) -> UserRead:
    raise NOT_IMPLEMENTED


@router.post("/login", response_model=TokenPair, summary="Iniciar sesión con correo y contraseña")
def login(payload: UserLogin) -> TokenPair:
    raise NOT_IMPLEMENTED


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
