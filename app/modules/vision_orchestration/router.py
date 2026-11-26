from fastapi import APIRouter, HTTPException, status

from app.core.errors import ErrorResponse
from app.modules.vision_orchestration.exceptions import ConsentRequiredError
from app.modules.vision_orchestration.schemas import FrameSubmission, VisionAnalysisResponse

router = APIRouter(prefix="/vision", tags=["vision-orchestration"])


@router.post(
    "/analyze",
    response_model=VisionAnalysisResponse,
    summary="Analizar un frame",
    responses={
        403: {
            "model": ErrorResponse,
            "description": "`consent_required`: falta el consentimiento o su versión (SCRUM-324).",
        },
        501: {"description": "La narración todavía no está implementada (SCRUM-38)."},
    },
)
def analyze_frame(payload: FrameSubmission) -> VisionAnalysisResponse:
    # SCRUM-324 / ADR-308: defensa adicional al cliente, que no envía imágenes sin
    # consentimiento. Se comprueba antes de mirar el frame: sin consentimiento no se procesa.
    if not payload.consent_given or not payload.consent_version:
        raise ConsentRequiredError()
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="No implementado")
