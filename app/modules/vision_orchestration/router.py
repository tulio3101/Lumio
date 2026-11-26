from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, UploadFile, status

from app.core.errors import ErrorResponse
from app.modules.narration.rate_limit import NarrationRateLimiterDep
from app.modules.narration.vlm import SceneDescriberDep
from app.modules.users.dependencies import CurrentUserId
from app.modules.vision_orchestration import service
from app.modules.vision_orchestration.image import MAX_IMAGE_BYTES
from app.modules.vision_orchestration.schemas import (
    NarrationTrigger,
    SceneLanguage,
    VisionAnalysisResponse,
)

router = APIRouter(prefix="/vision", tags=["vision-orchestration"])

_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Falta el access token o la sesión no es válida.",
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "`consent_required`: falta el consentimiento o su versión (SCRUM-324).",
    },
    status.HTTP_413_CONTENT_TOO_LARGE: {
        "model": ErrorResponse,
        "description": "`image_too_large`: más de 1 MB o más de 1024 px de lado largo.",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "`invalid_image`: la foto no es un JPEG, o un campo es inválido.",
    },
    status.HTTP_429_TOO_MANY_REQUESTS: {
        "model": ErrorResponse,
        "description": "`narration_rate_limited`: 1 solicitud cada 3 s y 1.500 al día por usuario.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "`narration_unavailable`: el VLM falló, está saturado o sin configurar.",
    },
    status.HTTP_504_GATEWAY_TIMEOUT: {
        "model": ErrorResponse,
        "description": "`narration_timeout`: el VLM tardó más de 4 s.",
    },
}


@router.post(
    "/analyze",
    response_model=VisionAnalysisResponse,
    summary="Describir el entorno a partir de una foto",
    description=(
        "Narración del entorno (SCRUM-38, ADR-308). Recibe una foto JPEG por "
        "`multipart/form-data` (≤ 1 MB, ≤ 1024 px de lado largo, sin metadatos) y devuelve una "
        "descripción corta en español lista para locutar como P3. La foto vive solo en memoria "
        "durante la solicitud: no se guarda en disco, base de datos ni logs, y tampoco la "
        "descripción. Sin `consent_version` responde 403 sin mirar la foto."
    ),
    responses=_RESPONSES,
)
def analyze_frame(
    user_id: CurrentUserId,
    describer: SceneDescriberDep,
    limiter: NarrationRateLimiterDep,
    image: Annotated[UploadFile, File(description="Foto JPEG del entorno.")],
    captured_at: Annotated[
        datetime, Form(description="Cuándo se tomó la foto; la app descarta respuestas viejas.")
    ],
    trigger: Annotated[NarrationTrigger, Form()] = NarrationTrigger.GESTURE,
    language: Annotated[SceneLanguage, Form()] = SceneLanguage.ES,
    consent_version: Annotated[
        str | None,
        Form(
            max_length=32,
            description=(
                "Versión del aviso de privacidad que aceptó el usuario (SCRUM-324). Sin ella la "
                "solicitud se rechaza con 403 `consent_required`."
            ),
        ),
    ] = None,
) -> VisionAnalysisResponse:
    # SCRUM-324 / ADR-308: defensa adicional al cliente, que no envía fotos sin
    # consentimiento. Se comprueba antes de leer la foto.
    service.require_consent(consent_version)
    # Se lee un byte de más para distinguir «justo 1 MB» de «más de 1 MB».
    data = image.file.read(MAX_IMAGE_BYTES + 1)
    try:
        return service.describe_scene(
            user_id=user_id,
            image=data,
            trigger=trigger,
            language=language,
            describer=describer,
            limiter=limiter,
        )
    finally:
        del data
        image.file.close()
