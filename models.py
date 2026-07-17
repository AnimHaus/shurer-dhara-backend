from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class Notice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str = ""
    title: str
    body: str
    imageUrl: Optional[str] = None
    likes: int = 0
    views: int = 0
    comments: int = 0
    tags: List[str] = Field(default_factory=list)
    active: bool = True
    pinned: bool = False
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NoticeCreate(BaseModel):
    title: str
    body: str
    imageUrl: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    active: bool = True
    pinned: bool = False


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    imageUrl: Optional[str] = None
    tags: Optional[List[str]] = None
    active: Optional[bool] = None
    pinned: Optional[bool] = None
    views: Optional[int] = None
    comments: Optional[int] = None


# ─── Gallery ──────────────────────────────────────────────────────────────────

class GalleryImage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    caption: Optional[str] = None
    category: str = "general"
    year: Optional[str] = None       # e.g. "2024" — for timeline filtering
    url: str          # CDN / R2 public URL
    key: str          # R2 object key (for deletion)
    order: int = 0
    active: bool = True
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GalleryImageCreate(BaseModel):
    title: str
    caption: Optional[str] = None
    category: str = "general"
    year: Optional[str] = None
    order: int = 0
    active: bool = True


class GalleryImageUpdate(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None
    category: Optional[str] = None
    year: Optional[str] = None
    order: Optional[int] = None
    active: Optional[bool] = None


# ─── Gallery Folders ──────────────────────────────────────────────────────────

class GalleryFolder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str          # URL-safe identifier used as the category value
    label: str         # Human-readable display name
    order: int = 0
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GalleryFolderCreate(BaseModel):
    label: str
    order: int = 0


class GalleryFolderUpdate(BaseModel):
    label: Optional[str] = None
    order: Optional[int] = None
