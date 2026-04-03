"""
Applications API router - Application submission and tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import structlog
import os

from app.database import get_db
from app.models import (
    Application, Job, ApplicationStatus, ApplicationType, 
    ATSPlatform, ApplicationLog, Resume
)
from app.services.ai_service import get_ai_service
from app.services.browser_service import get_browser_service
from app.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/")
async def list_applications(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List applications with optional filtering."""
    
    query = select(Application)
    
    if status:
        try:
            status_enum = ApplicationStatus(status)
            query = query.where(Application.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if job_id:
        query = query.where(Application.job_id == job_id)
    
    query = query.order_by(Application.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    return {
        "applications": [app_to_dict(app) for app in applications],
        "total": len(applications),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{application_id}")
async def get_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific application by ID."""
    
    result = await db.execute(
        select(Application)
        .where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return app_to_dict(application)


@router.post("/{job_id}/apply")
async def submit_application(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    cover_letter: Optional[str] = None,
):
    """
    Submit an application for a job.
    Triggers browser automation or email sending based on application type.
    """
    
    # Get job
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already applied
    existing_result = await db.execute(
        select(Application).where(Application.job_id == job_id)
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Already applied to this job. Status: {existing.status.value}"
        )
    
    # Get user's primary resume (simplified - would use actual user ID in production)
    resume_result = await db.execute(
        select(Resume).where(Resume.is_primary == True).limit(1)
    )
    resume = resume_result.scalar_one_or_none()
    
    if not resume:
        # Use default resume path
        resume_path = os.path.join(settings.RESUMES_DIR, "resume.pdf")
        if not os.path.exists(resume_path):
            raise HTTPException(
                status_code=400,
                detail="No resume found. Please upload a resume first."
            )
    else:
        resume_path = resume.file_path
    
    # Create application record
    application = Application(
        job_id=job_id,
        user_id=None,  # Would be set from auth context
        resume_id=resume.id if resume else None,
        application_type=job.application_type or ApplicationType.WEB_FORM,
        status=ApplicationStatus.PENDING,
        ats_platform=job.ats_platform,
    )
    
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    # Log the action
    log = ApplicationLog(
        job_id=job_id,
        application_id=application.id,
        action="application_initiated",
        status="pending",
        message=f"Application initiated for {job.title} at {job.company}",
    )
    db.add(log)
    await db.commit()
    
    # Trigger background application process
    background_tasks.add_task(
        process_application,
        str(application.id),
        cover_letter,
        resume_path,
    )
    
    return {
        "application_id": str(application.id),
        "status": "processing",
        "message": "Application submission initiated",
    }


async def process_application(
    application_id: str,
    cover_letter: Optional[str],
    resume_path: str,
):
    """
    Background task to process the actual application submission.
    Uses AI service and browser automation.
    """
    
    # This would be a Celery task in production
    logger.info("Processing application", application_id=application_id)
    
    # In production, this would:
    # 1. Fetch application, job, and personal context from DB
    # 2. Generate tailored content using AI service
    # 3. Execute browser automation or send email
    # 4. Update application status and create logs
    # 5. Handle fallback on failures
    
    pass  # Simplified for initial setup


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: str,
    status: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Manually update application status."""
    
    try:
        new_status = ApplicationStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = new_status
    if notes:
        application.notes = notes
    
    # Log the status change
    log = ApplicationLog(
        job_id=application.job_id,
        application_id=application_id,
        action="status_updated",
        status=status,
        message=f"Status manually updated to {status}",
    )
    db.add(log)
    await db.commit()
    
    return app_to_dict(application)


@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an application."""
    
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    await db.delete(application)
    await db.commit()
    
    return {"message": "Application deleted successfully"}


def app_to_dict(application: Application) -> dict:
    """Convert Application model to dictionary."""
    return {
        "id": str(application.id),
        "job_id": str(application.job_id),
        "user_id": str(application.user_id) if application.user_id else None,
        "resume_id": str(application.resume_id) if application.resume_id else None,
        "cover_letter": application.cover_letter,
        "email_content": application.email_content,
        "application_type": application.application_type.value,
        "status": application.status.value,
        "ats_platform": application.ats_platform.value if application.ats_platform else None,
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
        "last_attempt_at": application.last_attempt_at.isoformat() if application.last_attempt_at else None,
        "retry_count": application.retry_count,
        "model_used": application.model_used,
        "fallback_used": application.fallback_used,
        "success_verified": application.success_verified,
        "verification_screenshot_path": application.verification_screenshot_path,
        "notes": application.notes,
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }
