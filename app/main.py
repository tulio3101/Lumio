from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.modules.narration.router import router as narration_router
from app.modules.places.router import router as places_router
from app.modules.users.router import router as users_router
from app.modules.vision_orchestration.router import router as vision_orchestration_router
from app.modules.voice.router import router as voice_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Backend de Lumio. Los contratos de este OpenAPI son la referencia "
            "para el cliente iOS."
        ),
        debug=settings.debug,
        openapi_tags=[
            {"name": "health", "description": "Estado del servicio."},
            {"name": "users", "description": "Cuentas, autenticación y sesión."},
            {"name": "voice", "description": "Interpretación de comandos de voz."},
            {"name": "vision-orchestration", "description": "Análisis de frames del entorno."},
            {"name": "narration", "description": "Generación de narración para el usuario."},
            {"name": "places", "description": "Ruta activa e historial de rutas."},
        ],
    )
    register_exception_handlers(app)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    for router in (
        users_router,
        voice_router,
        vision_orchestration_router,
        narration_router,
        places_router,
    ):
        app.include_router(router)

    return app


app = create_app()
