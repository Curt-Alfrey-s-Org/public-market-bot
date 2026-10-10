"""
Assets API: list pics/videos in public/assets, upload from folder.
"""

import os
import logging
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException

from api.auth import require_admin  # writing files into the served assets: admin JWT only

logger = logging.getLogger(__name__)
router = APIRouter()

# Project root (parent of api/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "frontend" / "public" / "assets"
UPLOADS_DIR = ASSETS_DIR / "uploads"
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico"}
ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".ogg", ".mov", ".avi", ".mkv"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in ALLOWED_IMAGE_EXT


def _is_video(path: Path) -> bool:
    return path.suffix.lower() in ALLOWED_VIDEO_EXT


def _scan_assets(base: Path) -> list[dict]:
    out: list[dict] = []
    if not base.exists():
        return out
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext in ALLOWED_IMAGE_EXT:
            kind = "image"
        elif ext in ALLOWED_VIDEO_EXT:
            kind = "video"
        else:
            continue
        rel = p.relative_to(ASSETS_DIR)
        url_path = "/assets/" + rel.as_posix()
        out.append({
            "path": url_path,
            "name": p.name,
            "type": kind,
        })
    return out


@router.get("")
async def list_assets():
    """List pics and videos under frontend/public/assets (including uploads)."""
    files = _scan_assets(ASSETS_DIR)
    files.sort(key=lambda x: (x["name"].lower(), x["path"]))
    return {"files": files}


@router.post("/upload", dependencies=[Depends(require_admin)])
async def upload_assets(files: list[UploadFile] = File(...)):
    """Upload pics/videos from folder. Saves to assets/uploads. Returns URLs.

    Admin only (review 2026-09-25): any logged-in user could previously write up
    to 100 MB per file into the served assets folder.
    """
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    urls: list[str] = []
    for uf in files:
        if not uf.filename:
            continue
        path = Path(uf.filename)
        ext = path.suffix.lower()
        if ext not in ALLOWED_IMAGE_EXT and ext not in ALLOWED_VIDEO_EXT:
            logger.warning(f"Skip upload unsupported type: {uf.filename}")
            continue
        safe = re.sub(r"[^\w\-.]", "_", path.stem)[:80]
        base = f"{safe}_{uuid.uuid4().hex[:8]}{ext}"
        dest = UPLOADS_DIR / base
        try:
            contents = await uf.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(400, f"File too large: {uf.filename} (max {MAX_FILE_SIZE // (1024*1024)} MB)")
            dest.write_bytes(contents)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload write failed {uf.filename}: {e}")
            raise HTTPException(500, f"Upload failed: {uf.filename}")
        url = "/assets/uploads/" + base
        urls.append(url)
    return {"urls": urls}
