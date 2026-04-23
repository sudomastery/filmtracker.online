import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification, User)
        .join(User, Notification.actor_id == User.id)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(50)
    )
    rows = result.fetchall()

    items = []
    for notif, actor in rows:
        items.append({
            "id": notif.id,
            "type": notif.type,
            "is_read": notif.read,
            "created_at": notif.created_at,
            "entity_id": notif.entity_id,
            "actor": {
                "id": actor.id,
                "username": actor.username,
                "display_name": actor.display_name,
                "avatar_url": actor.avatar_url,
            },
        })

    unread_count = sum(1 for n, _ in rows if not n.read)
    return {"items": items, "unread_count": unread_count}


@router.patch("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.read == False)
        .values(read=True)
    )
    return {"detail": "All notifications marked as read"}


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notif = await db.scalar(
        select(Notification).where(Notification.id == notification_id)
    )
    if notif and notif.user_id == current_user.id:
        notif.read = True
        await db.flush()
    return {"detail": "Marked as read"}
