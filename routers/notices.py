from fastapi import APIRouter, HTTPException, Query, Request
from typing import List

from models import Notice, NoticeCreate, NoticeUpdate
import store


router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=List[Notice])
async def list_notices(request: Request, active: bool = Query(False)):
    return await store.get_notices(request.app.state.db, active_only=active)


@router.post("", response_model=Notice, status_code=201)
async def create_notice(request: Request, data: NoticeCreate):
    return await store.create_notice(request.app.state.db, data)


@router.get("/slug/{slug}", response_model=Notice)
async def get_notice_by_slug(request: Request, slug: str):
    notice = await store.get_notice_by_slug(request.app.state.db, slug)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice


@router.get("/{notice_id}", response_model=Notice)
async def get_notice(request: Request, notice_id: str):
    notice = await store.get_notice(request.app.state.db, notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice


@router.put("/{notice_id}", response_model=Notice)
async def replace_notice(request: Request, notice_id: str, data: NoticeCreate):
    update = NoticeUpdate(**data.model_dump())
    updated = await store.update_notice(request.app.state.db, notice_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Notice not found")
    return updated


@router.patch("/{notice_id}", response_model=Notice)
async def patch_notice(request: Request, notice_id: str, data: NoticeUpdate):
    updated = await store.update_notice(request.app.state.db, notice_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Notice not found")
    return updated


@router.post("/{notice_id}/like", response_model=Notice)
async def like_notice(request: Request, notice_id: str):
    notice = await store.like_notice(request.app.state.db, notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice


@router.post("/{notice_id}/view", response_model=Notice)
async def view_notice(request: Request, notice_id: str):
    notice = await store.increment_views(request.app.state.db, notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice


@router.post("/{notice_id}/comment", response_model=Notice)
async def comment_notice(request: Request, notice_id: str):
    notice = await store.increment_comments(request.app.state.db, notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice


@router.delete("/{notice_id}", status_code=204)
async def delete_notice(request: Request, notice_id: str):
    if not await store.delete_notice(request.app.state.db, notice_id):
        raise HTTPException(status_code=404, detail="Notice not found")
