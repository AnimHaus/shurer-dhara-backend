from fastapi import APIRouter, HTTPException, Request
from typing import List

from models import GalleryFolder, GalleryFolderCreate, GalleryFolderUpdate
import store

router = APIRouter(prefix="/api/gallery-folders", tags=["gallery-folders"])


@router.get("", response_model=List[GalleryFolder])
async def list_folders(request: Request):
    return await store.get_folders(request.app.state.db)


@router.post("", response_model=GalleryFolder, status_code=201)
async def create_folder(request: Request, data: GalleryFolderCreate):
    return await store.create_folder(request.app.state.db, data)


@router.get("/{folder_id}", response_model=GalleryFolder)
async def get_folder(request: Request, folder_id: str):
    folder = await store.get_folder(request.app.state.db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.patch("/{folder_id}", response_model=GalleryFolder)
async def patch_folder(request: Request, folder_id: str, data: GalleryFolderUpdate):
    updated = await store.update_folder(request.app.state.db, folder_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Folder not found")
    return updated


@router.delete("/{folder_id}", status_code=204)
async def delete_folder(request: Request, folder_id: str):
    """Deletes the folder. Images that used this category are NOT deleted — they retain the slug as a string."""
    if not await store.delete_folder(request.app.state.db, folder_id):
        raise HTTPException(status_code=404, detail="Folder not found")
