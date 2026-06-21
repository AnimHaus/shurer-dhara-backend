from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import re
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from models import Notice, NoticeCreate, NoticeUpdate


def _slugify(title: str, uid: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return f"{s[:60].rstrip('-')}-{uid[:8]}"


def _col(db: AsyncIOMotorDatabase):
    return db["news"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _doc_to_notice(doc: dict) -> Notice:
    doc.pop("_id", None)
    return Notice(**doc)


async def get_notices(db: AsyncIOMotorDatabase, active_only: bool = False) -> List[Notice]:
    query = {"active": True} if active_only else {}
    cursor = _col(db).find(query).sort([("pinned", -1), ("createdAt", -1)])
    return [_doc_to_notice(doc) async for doc in cursor]


async def get_notice(db: AsyncIOMotorDatabase, notice_id: str) -> Optional[Notice]:
    doc = await _col(db).find_one({"id": notice_id})
    return _doc_to_notice(doc) if doc else None


async def get_notice_by_slug(db: AsyncIOMotorDatabase, slug: str) -> Optional[Notice]:
    doc = await _col(db).find_one({"slug": slug})
    return _doc_to_notice(doc) if doc else None


async def create_notice(db: AsyncIOMotorDatabase, data: NoticeCreate) -> Notice:
    now = _now()
    uid = str(uuid.uuid4())
    notice = Notice(
        id=uid,
        slug=_slugify(data.title, uid),
        title=data.title,
        body=data.body,
        imageUrl=data.imageUrl,
        tags=data.tags,
        active=data.active,
        pinned=data.pinned,
        createdAt=now,
        updatedAt=now,
    )
    await _col(db).insert_one(notice.model_dump())
    return notice


async def update_notice(db: AsyncIOMotorDatabase, notice_id: str, data: NoticeUpdate) -> Optional[Notice]:
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
    if not changes:
        return await get_notice(db, notice_id)
    changes["updatedAt"] = _now()
    result = await _col(db).find_one_and_update(
        {"id": notice_id},
        {"$set": changes},
        return_document=True,
    )
    return _doc_to_notice(result) if result else None


async def like_notice(db: AsyncIOMotorDatabase, notice_id: str) -> Optional[Notice]:
    result = await _col(db).find_one_and_update(
        {"id": notice_id},
        {"$inc": {"likes": 1}, "$set": {"updatedAt": _now()}},
        return_document=True,
    )
    return _doc_to_notice(result) if result else None


async def increment_views(db: AsyncIOMotorDatabase, notice_id: str) -> Optional[Notice]:
    result = await _col(db).find_one_and_update(
        {"id": notice_id},
        {"$inc": {"views": 1}},
        return_document=True,
    )
    return _doc_to_notice(result) if result else None


async def increment_comments(db: AsyncIOMotorDatabase, notice_id: str) -> Optional[Notice]:
    result = await _col(db).find_one_and_update(
        {"id": notice_id},
        {"$inc": {"comments": 1}},
        return_document=True,
    )
    return _doc_to_notice(result) if result else None


async def delete_notice(db: AsyncIOMotorDatabase, notice_id: str) -> bool:
    result = await _col(db).delete_one({"id": notice_id})
    return result.deleted_count > 0
