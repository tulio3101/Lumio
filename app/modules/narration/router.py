from fastapi import APIRouter, HTTPException, status

from app.modules.narration.schemas import NarrationRequest, NarrationResponse

router = APIRouter(prefix="/narration", tags=["narration"])


@router.post("", response_model=NarrationResponse, summary="Generar narración")
def narrate(payload: NarrationRequest) -> NarrationResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="No implementado")
