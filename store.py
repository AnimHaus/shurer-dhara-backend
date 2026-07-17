from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import re
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from models import Notice, NoticeCreate, NoticeUpdate, GalleryImage, GalleryImageCreate, GalleryImageUpdate, GalleryFolder, GalleryFolderCreate, GalleryFolderUpdate


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


# ─── Gallery store ────────────────────────────────────────────────────────────

def _gallery_col(db: AsyncIOMotorDatabase):
    return db["gallery"]


def _doc_to_image(doc: dict) -> GalleryImage:
    doc.pop("_id", None)
    return GalleryImage(**doc)


async def get_gallery_images(db: AsyncIOMotorDatabase, active_only: bool = False) -> List[GalleryImage]:
    query = {"active": True} if active_only else {}
    cursor = _gallery_col(db).find(query).sort([("order", 1), ("createdAt", -1)])
    return [_doc_to_image(doc) async for doc in cursor]


async def get_gallery_image(db: AsyncIOMotorDatabase, image_id: str) -> Optional[GalleryImage]:
    doc = await _gallery_col(db).find_one({"id": image_id})
    return _doc_to_image(doc) if doc else None


async def create_gallery_image(
    db: AsyncIOMotorDatabase,
    data: GalleryImageCreate,
    url: str,
    key: str,
) -> GalleryImage:
    now = _now()
    image = GalleryImage(
        title=data.title,
        caption=data.caption,
        category=data.category,
        year=data.year,
        order=data.order,
        active=data.active,
        url=url,
        key=key,
        createdAt=now,
        updatedAt=now,
    )
    await _gallery_col(db).insert_one(image.model_dump())
    return image


async def update_gallery_image(
    db: AsyncIOMotorDatabase,
    image_id: str,
    data: GalleryImageUpdate,
) -> Optional[GalleryImage]:
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
    if not changes:
        return await get_gallery_image(db, image_id)
    changes["updatedAt"] = _now()
    result = await _gallery_col(db).find_one_and_update(
        {"id": image_id},
        {"$set": changes},
        return_document=True,
    )
    return _doc_to_image(result) if result else None


async def delete_gallery_image(db: AsyncIOMotorDatabase, image_id: str) -> Optional[str]:
    """Delete the DB record and return the R2 key so the caller can delete from R2."""
    doc = await _gallery_col(db).find_one_and_delete({"id": image_id})
    return doc["key"] if doc else None


# ─── Gallery Folder store ─────────────────────────────────────────────────────

def _folder_col(db: AsyncIOMotorDatabase):
    return db["gallery_folders"]


def _doc_to_folder(doc: dict) -> GalleryFolder:
    doc.pop("_id", None)
    return GalleryFolder(**doc)


def _slugify_folder(label: str, uid: str) -> str:
    s = re.sub(r"[^\w\s-]", "", label.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return f"{s[:40].rstrip('-')}"


async def get_folders(db: AsyncIOMotorDatabase) -> List[GalleryFolder]:
    cursor = _folder_col(db).find().sort("order", 1)
    return [_doc_to_folder(doc) async for doc in cursor]


async def get_folder(db: AsyncIOMotorDatabase, folder_id: str) -> Optional[GalleryFolder]:
    doc = await _folder_col(db).find_one({"id": folder_id})
    return _doc_to_folder(doc) if doc else None


async def get_folder_by_slug(db: AsyncIOMotorDatabase, slug: str) -> Optional[GalleryFolder]:
    doc = await _folder_col(db).find_one({"slug": slug})
    return _doc_to_folder(doc) if doc else None


async def create_folder(db: AsyncIOMotorDatabase, data: GalleryFolderCreate) -> GalleryFolder:
    now = _now()
    uid = str(uuid.uuid4())
    slug = _slugify_folder(data.label, uid)
    # Ensure slug uniqueness by appending short uid if collision
    existing = await get_folder_by_slug(db, slug)
    if existing:
        slug = f"{slug}-{uid[:6]}"
    folder = GalleryFolder(
        id=uid,
        slug=slug,
        label=data.label,
        order=data.order,
        createdAt=now,
        updatedAt=now,
    )
    await _folder_col(db).insert_one(folder.model_dump())
    return folder


async def update_folder(db: AsyncIOMotorDatabase, folder_id: str, data: GalleryFolderUpdate) -> Optional[GalleryFolder]:
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
    if not changes:
        return await get_folder(db, folder_id)
    changes["updatedAt"] = _now()
    result = await _folder_col(db).find_one_and_update(
        {"id": folder_id},
        {"$set": changes},
        return_document=True,
    )
    return _doc_to_folder(result) if result else None


async def delete_folder(db: AsyncIOMotorDatabase, folder_id: str) -> bool:
    result = await _folder_col(db).delete_one({"id": folder_id})
    return result.deleted_count > 0
