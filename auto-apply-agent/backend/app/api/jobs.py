"""
Jobs API router - Job collection, listing, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from datetime import datetime
import structlog

from app.database import get_db
from app.models import Job, ApplicationStatus, ApplicationType, ATSPlatform
from app.services.ai_service import get_ai_service

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    min_match_score: Optional[float] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List jobs with optional filtering."""
    
    query = select(Job)
    
    # Apply filters
    if status:
        try:
            status_enum = ApplicationStatus(status)
            query = query.where(Job.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    if source:
        query = query.where(Job.source == source)
    
    if min_match_score is not None:
        query = query.where(Job.match_score >= min_match_score)
    
    # Order by match score and collection date
    query = query.order_by(Job.match_score.desc(), Job.collected_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return {
        "jobs": [job_to_dict(job) for job in jobs],
        "total": len(jobs),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific job by ID."""
    
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_to_dict(job)


@router.post("/collect")
async def collect_jobs(
    keywords: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger job collection from configured sources.
    In production, this would be handled by Celery beat scheduled tasks.
    """
    
    ai_service = get_ai_service()
    
    # This is a simplified version - full implementation would call Adzuna/Jooble APIs
    logger.info("Job collection triggered", keywords=keywords, location=location)
    
    return {
        "message": "Job collection initiated",
        "status": "processing",
        "note": "In production, this triggers a Celery task to poll job APIs",
    }


@router.post("/{job_id}/analyze")
async def analyze_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Analyze a job description using AI."""
    
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    ai_service = get_ai_service()
    
    analysis = await ai_service.analyze_job_description(
        job_title=job.title,
        company=job.company,
        description=job.description or "",
        requirements=job.requirements or "",
    )
    
    if not analysis["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {analysis['error']}",
        )
    
    # Update job with analysis results
    # In production, parse JSON response and update fields
    
    return {
        "job_id": str(job.id),
        "analysis": analysis["response"],
        "model_used": analysis["model_used"],
        "fallback_used": analysis["fallback_used"],
    }


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a job and its associated applications."""
    
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.delete(job)
    await db.commit()
    
    return {"message": "Job deleted successfully"}


def job_to_dict(job: Job) -> dict:
    """Convert Job model to dictionary."""
    return {
        "id": str(job.id),
        "external_id": job.external_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "remote_type": job.remote_type,
        "description": job.description,
        "requirements": job.requirements,
        "salary_min": float(job.salary_min) if job.salary_min else None,
        "salary_max": float(job.salary_max) if job.salary_max else None,
        "currency": job.currency,
        "apply_url": job.apply_url,
        "application_type": job.application_type.value if job.application_type else None,
        "ats_platform": job.ats_platform.value if job.ats_platform else None,
        "source": job.source,
        "match_score": job.match_score,
        "status": job.status.value if job.status else None,
        "collected_at": job.collected_at.isoformat() if job.collected_at else None,
        "applied_at": job.applied_at.isoformat() if job.applied_at else None,
    }
