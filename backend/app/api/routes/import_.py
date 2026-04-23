import uuid
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, get_redis
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.import_ import ImportRequest, ImportStatus, ImportResults
from app.services import import_ as import_service

router = APIRouter(prefix="/import", tags=["import"])

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


@router.post("/txt", response_model=ImportRequest, status_code=202)
async def upload_txt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 1MB)")

    text = content.decode("utf-8", errors="replace")
    lines = import_service.parse_lines(text)

    if not lines:
        raise HTTPException(status_code=400, detail="No movie titles found in file")

    job_id = str(uuid.uuid4())
    await redis.hset(f"import:{job_id}", mapping={
        "status": "pending",
        "total": len(lines),
        "processed": 0,
        "matched": 0,
        "unmatched": 0,
    })
    await redis.expire(f"import:{job_id}", 3600)

    # Run import in background (asyncio task — no Celery needed for dev)
    asyncio.create_task(
        import_service.process_import(job_id, lines, str(current_user.id), redis, db)
    )

    return ImportRequest(job_id=job_id)


@router.get("/{job_id}/status", response_model=ImportStatus)
async def get_import_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    data = await redis.hgetall(f"import:{job_id}")
    if not data:
        raise HTTPException(status_code=404, detail="Import job not found")

    return ImportStatus(
        job_id=job_id,
        status=data.get("status", "unknown"),
        total=int(data.get("total", 0)),
        processed=int(data.get("processed", 0)),
        matched=int(data.get("matched", 0)),
        unmatched=int(data.get("unmatched", 0)),
    )


@router.get("/{job_id}/results", response_model=ImportResults)
async def get_import_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    import json
    raw = await redis.get(f"import:{job_id}:results")
    if not raw:
        raise HTTPException(status_code=404, detail="Results not ready yet")

    return ImportResults(job_id=job_id, results=json.loads(raw))
