"""Cloudflare R2 helpers (boto3 S3-compatible)."""

import os
import uuid
import mimetypes
import boto3
from botocore.config import Config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT_URL"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name=os.environ.get("R2_REGION", "auto"),
            config=Config(signature_version="s3v4"),
        )
    return _client


BUCKET = lambda: os.environ["R2_BUCKET_NAME"]
CDN_BASE = lambda: os.environ.get("CDN_BASE_URL", os.environ["R2_PUBLIC_BASE_URL"]).rstrip("/")


def upload_image(file_bytes: bytes, original_filename: str, prefix: str = "gallery") -> tuple[str, str]:
    """Upload bytes to R2. Returns (public_url, object_key)."""
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "jpg"
    key = f"{prefix}/{uuid.uuid4()}.{ext}"
    content_type = mimetypes.guess_type(original_filename)[0] or "image/jpeg"

    _get_client().put_object(
        Bucket=BUCKET(),
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )

    url = f"{CDN_BASE()}/{key}"
    return url, key


def delete_image(key: str) -> None:
    """Delete an object from R2 by its key. Silently ignores missing objects."""
    try:
        _get_client().delete_object(Bucket=BUCKET(), Key=key)
    except Exception:
        pass
