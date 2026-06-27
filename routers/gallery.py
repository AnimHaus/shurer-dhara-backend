from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, File, Form
from typing import List, Optional

from models import GalleryImage, GalleryImageCreate, GalleryImageUpdate
import store
import r2

router = APIRouter(prefix="/api/gallery", tags=["gallery"])

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


def _validate_image(file: UploadFile) -> None:
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported image type. Use JPEG, PNG, WEBP, or GIF.")


@router.get("", response_model=List[GalleryImage])
async def list_images(request: Request, active: bool = Query(False)):
    return await store.get_gallery_images(request.app.state.db, active_only=active)


@router.post("", response_model=GalleryImage, status_code=201)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    caption: Optional[str] = Form(None),
    category: str = Form("general"),
    order: int = Form(0),
    active: bool = Form(True),
):
    _validate_image(file)
    file_bytes = await file.read()
    if len(file_bytes) > _MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    url, key = r2.upload_image(file_bytes, file.filename or "image.jpg")
    data = GalleryImageCreate(
        title=title,
        caption=caption,
        category=category,
        order=order,
        active=active,
    )
    return await store.create_gallery_image(request.app.state.db, data, url=url, key=key)


@router.get("/{image_id}", response_model=GalleryImage)
async def get_image(request: Request, image_id: str):
    image = await store.get_gallery_image(request.app.state.db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.patch("/{image_id}", response_model=GalleryImage)
async def patch_image(request: Request, image_id: str, data: GalleryImageUpdate):
    updated = await store.update_gallery_image(request.app.state.db, image_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Image not found")
    return updated


@router.delete("/{image_id}", status_code=204)
async def delete_image(request: Request, image_id: str):
    key = await store.delete_gallery_image(request.app.state.db, image_id)
    if key is None:
        raise HTTPException(status_code=404, detail="Image not found")
    r2.delete_image(key)
