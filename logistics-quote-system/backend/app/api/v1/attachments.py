# backend/app/api/v1/attachments.py
"""
路线附件管理（上传/列表/下载/删除）
支持：图片(jpg/png/gif/webp)、PDF、Word(doc/docx)、Excel(xls/xlsx)
"""
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...core.deps import get_db, get_current_user
from ...models.user import User

router = APIRouter(prefix="/attachments", tags=["附件管理"])

UPLOAD_BASE = Path(__file__).parent.parent.parent.parent / "uploads"

ALLOWED_EXTENSIONS = {
    ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".gif": "image", ".webp": "image",
    ".pdf": "pdf",
    ".doc": "word", ".docx": "word",
    ".xls": "excel", ".xlsx": "excel",
}

MAX_SIZE = 20 * 1024 * 1024  # 20MB


def _get_upload_dir(route_id: int) -> Path:
    d = UPLOAD_BASE / str(route_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/upload/{route_id}", summary="上传附件")
async def upload_attachment(
    route_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型：{ext}，仅支持图片/PDF/Word/Excel")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件超过20MB限制")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    save_path = _get_upload_dir(route_id) / stored_name
    save_path.write_bytes(content)

    db.execute(text("""
        INSERT INTO route_attachments (route_id, original_name, stored_name, file_size, file_type, uploader)
        VALUES (:route_id, :original_name, :stored_name, :file_size, :file_type, :uploader)
    """), {
        "route_id": route_id,
        "original_name": file.filename,
        "stored_name": stored_name,
        "file_size": len(content),
        "file_type": ALLOWED_EXTENSIONS[ext],
        "uploader": current_user.username,
    })
    db.commit()

    row = db.execute(text(
        "SELECT attachment_id, upload_time FROM route_attachments WHERE stored_name = :s"
    ), {"s": stored_name}).fetchone()

    return {
        "attachment_id": row[0],
        "original_name": file.filename,
        "file_type": ALLOWED_EXTENSIONS[ext],
        "file_size": len(content),
        "upload_time": str(row[1]),
    }


@router.get("/route/{route_id}", summary="获取路线附件列表")
async def list_attachments(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rows = db.execute(text("""
        SELECT attachment_id, original_name, file_size, file_type, upload_time, uploader
        FROM route_attachments
        WHERE route_id = :route_id
        ORDER BY upload_time DESC
    """), {"route_id": route_id}).fetchall()

    return [
        {
            "attachment_id": r[0],
            "original_name": r[1],
            "file_size": r[2],
            "file_type": r[3],
            "upload_time": str(r[4]),
            "uploader": r[5],
        }
        for r in rows
    ]


@router.get("/{attachment_id}/download", summary="下载/预览附件")
async def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = db.execute(text("""
        SELECT route_id, original_name, stored_name, file_type
        FROM route_attachments WHERE attachment_id = :id
    """), {"id": attachment_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="附件不存在")

    file_path = UPLOAD_BASE / str(row[0]) / row[2]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件已被删除")

    # 图片和PDF在浏览器内预览，其余触发下载
    inline_types = {"image", "pdf"}
    disposition = "inline" if row[3] in inline_types else "attachment"

    return FileResponse(
        path=str(file_path),
        filename=row[1],
        headers={"Content-Disposition": f'{disposition}; filename="{row[1]}"'}
    )


@router.delete("/{attachment_id}", summary="删除附件")
async def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    row = db.execute(text("""
        SELECT route_id, stored_name FROM route_attachments WHERE attachment_id = :id
    """), {"id": attachment_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="附件不存在")

    file_path = UPLOAD_BASE / str(row[0]) / row[1]
    if file_path.exists():
        file_path.unlink()

    db.execute(text("DELETE FROM route_attachments WHERE attachment_id = :id"), {"id": attachment_id})
    db.commit()

    return {"success": True}
