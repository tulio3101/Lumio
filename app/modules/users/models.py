import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # Null para cuentas creadas solo con Google.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    # Datos de perfil (Personalizar Cuenta), opcionales. Ver UserProfileUpdate.
    display_name: Mapped[str | None] = mapped_column(String(60))
    # Celular colombiano: 10 dígitos que empiezan por 3, sin prefijo.
    phone: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthSession(Base):
    """Sesión de un dispositivo; su id es el claim `jti` de los tokens emitidos."""

    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordResetCode(Base):
    """Código de Recuperar Contraseña. Solo se guarda su hash y solo vale el último de la
    cuenta. ON DELETE CASCADE: Eliminar Cuenta (SCRUM-7) los borra."""

    __tablename__ = "password_reset_codes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    code_hash: Mapped[str] = mapped_column(String(255))
    # Intentos fallidos; al llegar al máximo el código deja de servir.
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserPreferences(Base):
    """Preferencias de voz y vibración de la cuenta (Configurar Preferencias de Voz
    Descriptiva y Configurar Retroalimentación Háptica). Es una copia de respaldo: el teléfono
    las lee siempre de su almacenamiento local y las sincroniza en segundo plano, para
    recuperarlas al reinstalar la app o entrar desde otro teléfono.
    """

    __tablename__ = "user_preferences"

    # Una fila por cuenta. ON DELETE CASCADE: Eliminar Cuenta (SCRUM-7) las borra.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    voice_language: Mapped[str] = mapped_column(String(16))
    # Identificador de la voz del sistema; solo el teléfono sabe si está instalada.
    voice_identifier: Mapped[str | None] = mapped_column(String(255))
    speech_rate: Mapped[float] = mapped_column(Float)
    haptics_enabled: Mapped[bool] = mapped_column(Boolean)
    haptic_intensity: Mapped[str] = mapped_column(String(16))
    # Eventos configurables apagados; las alertas de seguridad no se pueden apagar.
    haptic_disabled_events: Mapped[list[str]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
