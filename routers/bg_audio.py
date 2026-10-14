from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from pydantic import BaseModel, Field
import r2
import store

router = APIRouter(prefix="/api/bg-audio", tags=["bg-audio"])

_ALLOWED_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/flac"}
_MAX_SIZE = 50 * 1024 * 1024  # 50 MB


class VolumeUpdate(BaseModel):
    volume: float = Field(..., ge=0.0, le=1.0)


@router.get("")
async def get_audio_info(request: Request):
    """Return the current background audio public URL and volume level."""
    db = getattr(request.app.state, "db", None)
    volume = 0.5
    if db is not None:
        settings = await store.get_bg_audio_settings(db)
        volume = settings.get("volume", 0.5)
    return {"url": r2.get_audio_url(), "volume": volume}


@router.patch("/volume")
async def update_audio_volume(data: VolumeUpdate, request: Request):
    """Update background audio default volume (0.0 to 1.0)."""
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    res = await store.update_bg_audio_volume(db, data.volume)
    return {"volume": res["volume"], "message": "Volume updated successfully."}


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Replace the background audio file. Accepts MP3, WAV, OGG, FLAC."""
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported audio type. Use MP3, WAV, OGG, or FLAC.",
        )
    file_bytes = await file.read()
    if len(file_bytes) > _MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50 MB.")

    url = r2.upload_audio(file_bytes)
    return {"url": url, "message": "Background audio updated successfully."}
