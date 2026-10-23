from fastapi import APIRouter, HTTPException, status

from app.modules.vision_orchestration.schemas import FrameSubmission, VisionAnalysisResponse

router = APIRouter(prefix="/vision", tags=["vision-orchestration"])


@router.post("/analyze", response_model=VisionAnalysisResponse, summary="Analizar un frame")
def analyze_frame(payload: FrameSubmission) -> VisionAnalysisResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="No implementado")
