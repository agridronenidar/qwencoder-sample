"""
Preferences API router - User preference management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import structlog

from app.database import get_db
from app.models import UserPreference
from app.api.auth import get_current_user
from app.models import UserProfile

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/")
async def get_preferences(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's preferences."""
    
    result = await db.execute(
        select(UserPreference)
        .where(UserPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        # Create default preferences
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    
    return {
        "id": str(prefs.id),
        "max_daily_applications": prefs.max_daily_applications,
        "min_match_score": prefs.min_match_score,
        "auto_approve_high_match": prefs.auto_approve_high_match,
        "preferred_locations": prefs.preferred_locations,
        "remote_only": prefs.remote_only,
        "excluded_companies": prefs.excluded_companies,
        "keywords_include": prefs.keywords_include,
        "keywords_exclude": prefs.keywords_exclude,
        "notification_email": prefs.notification_email,
    }


@router.put("/")
async def update_preferences(
    max_daily_applications: Optional[int] = None,
    min_match_score: Optional[float] = None,
    auto_approve_high_match: Optional[bool] = None,
    preferred_locations: Optional[List[str]] = None,
    remote_only: Optional[bool] = None,
    excluded_companies: Optional[List[str]] = None,
    keywords_include: Optional[List[str]] = None,
    keywords_exclude: Optional[List[str]] = None,
    notification_email: Optional[bool] = None,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences."""
    
    result = await db.execute(
        select(UserPreference)
        .where(UserPreference.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
    
    # Update fields if provided
    if max_daily_applications is not None:
        prefs.max_daily_applications = max_daily_applications
    if min_match_score is not None:
        prefs.min_match_score = min_match_score
    if auto_approve_high_match is not None:
        prefs.auto_approve_high_match = auto_approve_high_match
    if preferred_locations is not None:
        prefs.preferred_locations = preferred_locations
    if remote_only is not None:
        prefs.remote_only = remote_only
    if excluded_companies is not None:
        prefs.excluded_companies = excluded_companies
    if keywords_include is not None:
        prefs.keywords_include = keywords_include
    if keywords_exclude is not None:
        prefs.keywords_exclude = keywords_exclude
    if notification_email is not None:
        prefs.notification_email = notification_email
    
    await db.commit()
    await db.refresh(prefs)
    
    return {
        "id": str(prefs.id),
        "max_daily_applications": prefs.max_daily_applications,
        "min_match_score": prefs.min_match_score,
        "auto_approve_high_match": prefs.auto_approve_high_match,
        "preferred_locations": prefs.preferred_locations,
        "remote_only": prefs.remote_only,
        "excluded_companies": prefs.excluded_companies,
        "keywords_include": prefs.keywords_include,
        "keywords_exclude": prefs.keywords_exclude,
        "notification_email": prefs.notification_email,
        "message": "Preferences updated successfully",
    }
