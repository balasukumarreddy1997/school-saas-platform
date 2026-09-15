"""Announcements API endpoints."""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_async_session
from app.models.user import User, UserRole
from app.models.announcement import Announcement
from app.core.security import get_current_user

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    type: str = "general"
    target_audience: str = "all"
    is_pinned: bool = False
    expires_at: Optional[datetime] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    target_audience: Optional[str] = None
    is_pinned: Optional[bool] = None
    expires_at: Optional[datetime] = None


@router.get("/")
async def get_announcements(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get announcements for the current user based on their role."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')

    # Get user role
    result = await session.execute(
        select(UserRole).where(UserRole.user_id == current_user.id)
    )
    user_role = result.scalar_one_or_none()
    role = user_role.role if user_role else "student"

    # Build query based on role
    now = datetime.utcnow()
    query = select(Announcement).where(
        and_(
            Announcement.school_id == school_id_str,
            Announcement.is_active == True,
            or_(
                Announcement.expires_at == None,
                Announcement.expires_at > now,
            ),
            or_(
                Announcement.target_audience == "all",
                Announcement.target_audience == role + "s",  # students, teachers
            ),
        )
    ).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())

    result = await session.execute(query)
    announcements = result.scalars().all()

    # Get creator names
    response = []
    for ann in announcements:
        creator_name = "Admin"
        try:
            creator_result = await session.execute(
                select(User).where(User.id == ann.created_by)
            )
            creator = creator_result.scalar_one_or_none()
            if creator:
                creator_name = f"{creator.first_name} {creator.last_name}"
        except:
            pass

        response.append({
            "id": ann.id,
            "title": ann.title,
            "content": ann.content,
            "type": ann.type,
            "target_audience": ann.target_audience,
            "is_pinned": ann.is_pinned,
            "created_by": creator_name,
            "created_at": ann.created_at.isoformat(),
            "expires_at": ann.expires_at.isoformat() if ann.expires_at else None,
        })

    return response


@router.get("/recent")
async def get_recent_announcements(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get recent announcements for dashboard."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')

    now = datetime.utcnow()
    query = select(Announcement).where(
        and_(
            Announcement.school_id == school_id_str,
            Announcement.is_active == True,
            or_(
                Announcement.expires_at == None,
                Announcement.expires_at > now,
            ),
        )
    ).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).limit(limit)

    result = await session.execute(query)
    announcements = result.scalars().all()

    return [
        {
            "id": ann.id,
            "title": ann.title,
            "type": ann.type,
            "is_pinned": ann.is_pinned,
            "created_at": ann.created_at.isoformat(),
        }
        for ann in announcements
    ]


# Admin endpoints
@router.get("/all")
async def get_all_announcements(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get all announcements (admin)."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')

    query = select(Announcement).where(
        Announcement.school_id == school_id_str,
    ).order_by(Announcement.created_at.desc())

    result = await session.execute(query)
    announcements = result.scalars().all()

    response = []
    for ann in announcements:
        creator_name = "Admin"
        try:
            creator_result = await session.execute(
                select(User).where(User.id == ann.created_by)
            )
            creator = creator_result.scalar_one_or_none()
            if creator:
                creator_name = f"{creator.first_name} {creator.last_name}"
        except:
            pass

        response.append({
            "id": ann.id,
            "title": ann.title,
            "content": ann.content,
            "type": ann.type,
            "target_audience": ann.target_audience,
            "is_pinned": ann.is_pinned,
            "is_active": ann.is_active,
            "created_by": creator_name,
            "created_at": ann.created_at.isoformat(),
            "expires_at": ann.expires_at.isoformat() if ann.expires_at else None,
        })

    return response


@router.post("/")
async def create_announcement(
    data: AnnouncementCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new announcement (admin)."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')
    user_id_str = current_user.id.hex if hasattr(current_user.id, 'hex') else str(current_user.id).replace('-', '')

    announcement = Announcement(
        school_id=school_id_str,
        title=data.title,
        content=data.content,
        type=data.type,
        target_audience=data.target_audience,
        is_pinned=data.is_pinned,
        expires_at=data.expires_at,
        created_by=user_id_str,
    )
    session.add(announcement)
    await session.commit()
    await session.refresh(announcement)

    return {"id": announcement.id, "message": "Announcement created"}


@router.put("/{announcement_id}")
async def update_announcement(
    announcement_id: str,
    data: AnnouncementUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update an announcement (admin)."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')

    result = await session.execute(
        select(Announcement).where(
            and_(
                Announcement.id == announcement_id,
                Announcement.school_id == school_id_str,
            )
        )
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if data.title is not None:
        announcement.title = data.title
    if data.content is not None:
        announcement.content = data.content
    if data.type is not None:
        announcement.type = data.type
    if data.target_audience is not None:
        announcement.target_audience = data.target_audience
    if data.is_pinned is not None:
        announcement.is_pinned = data.is_pinned
    if data.expires_at is not None:
        announcement.expires_at = data.expires_at

    announcement.updated_at = datetime.utcnow()
    await session.commit()

    return {"message": "Announcement updated"}


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete an announcement (admin)."""
    school_id_str = current_user.school_id.hex if hasattr(current_user.school_id, 'hex') else str(current_user.school_id).replace('-', '')

    result = await session.execute(
        select(Announcement).where(
            and_(
                Announcement.id == announcement_id,
                Announcement.school_id == school_id_str,
            )
        )
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    announcement.is_active = False
    await session.commit()

    return {"message": "Announcement deleted"}
