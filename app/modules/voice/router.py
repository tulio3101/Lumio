from fastapi import APIRouter, HTTPException, status

from app.modules.voice.schemas import VoiceCommandRequest, VoiceCommandResponse

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/commands", response_model=VoiceCommandResponse, summary="Interpretar comando de voz")
def interpret_command(payload: VoiceCommandRequest) -> VoiceCommandResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="No implementado")
