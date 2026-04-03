"""
Users API router - User profile management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import structlog

from app.database import get_db
from app.models import UserProfile, Resume, PersonalContext
from app.api.auth import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/profile")
async def get_profile(
    current_user: UserProfile = Depends(get_current_user),
):
    """Get current user's profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.put("/profile")
async def update_profile(
    full_name: Optional[str] = None,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    
    if full_name:
        current_user.full_name = full_name
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
    }


@router.get("/resumes")
async def list_resumes(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all resumes for the current user."""
    
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    
    return {
        "resumes": [
            {
                "id": str(r.id),
                "filename": r.filename,
                "file_type": r.file_type,
                "is_primary": r.is_primary,
                "tags": r.tags,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in resumes
        ]
    }


@router.get("/context")
async def get_personal_context(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's personal context data for RAG."""
    
    result = await db.execute(
        select(PersonalContext)
        .where(PersonalContext.user_id == current_user.id)
    )
    contexts = result.scalars().all()
    
    return {
        "context": {
            ctx.data_key: ctx.data_value
            for ctx in contexts
        }
    }


@router.put("/context/{data_key}")
async def update_personal_context(
    data_key: str,
    data_value: dict,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update or create personal context data."""
    
    result = await db.execute(
        select(PersonalContext)
        .where(PersonalContext.user_id == current_user.id)
        .where(PersonalContext.data_key == data_key)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.data_value = data_value
    else:
        new_context = PersonalContext(
            user_id=current_user.id,
            data_key=data_key,
            data_value=data_value,
        )
        db.add(new_context)
    
    await db.commit()
    
    return {"message": f"Context '{data_key}' updated successfully"}
