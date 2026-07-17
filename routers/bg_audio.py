from fastapi import APIRouter, HTTPException, UploadFile, File, Request
import r2

router = APIRouter(prefix="/api/bg-audio", tags=["bg-audio"])

_ALLOWED_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/flac"}
_MAX_SIZE = 50 * 1024 * 1024  # 50 MB


@router.get("")
def get_audio_url():
    """Return the current background audio public URL."""
    return {"url": r2.get_audio_url()}


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
