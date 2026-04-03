"""
SQLAlchemy ORM models for the AutoApply Agent database.
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, 
    ForeignKey, Enum, DECIMAL, ARRAY, JSONB
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()


# Enum Types
class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    COLLECTING = "collecting"
    READY_TO_APPLY = "ready_to_apply"
    APPLYING = "applying"
    APPLIED = "applied"
    INTERVIEW_REQUESTED = "interview_requested"
    REJECTED = "rejected"
    OFFER_RECEIVED = "offer_received"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    FAILED = "failed"


class ApplicationType(enum.Enum):
    WEB_FORM = "web_form"
    DIRECT_EMAIL = "direct_email"
    LINKEDIN_EASY_APPLY = "linkedin_easy_apply"
    COMPANY_PORTAL = "company_portal"


class ATSPlatform(enum.Enum):
    LEVER = "lever"
    GREENHOUSE = "greenhouse"
    WORKDAY = "workday"
    ICIMS = "icims"
    ASHBY = "ashby"
    OTHER = "other"
    UNKNOWN = "unknown"


# Models
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    personal_context = relationship("PersonalContext", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), default="pdf")
    is_primary = Column(Boolean, default=False)
    tags = Column(ARRAY(String))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("UserProfile", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")


class PersonalContext(Base):
    __tablename__ = "personal_context"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    data_key = Column(String(100), nullable=False)  # experience, projects, skills, education
    data_value = Column(JSONB, nullable=False)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("UserProfile", back_populates="personal_context")

    __table_args__ = (
        # Unique constraint on user_id and data_key
        __import__('sqlalchemy').UniqueConstraint('user_id', 'data_key', name='uq_user_data_key'),
    )


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), index=True)
    title = Column(String(500), nullable=False)
    company = Column(String(500), nullable=False)
    location = Column(String(500))
    remote_type = Column(String(100))  # fully_remote, hybrid, onsite
    description = Column(Text)
    requirements = Column(Text)
    salary_min = Column(DECIMAL(12, 2))
    salary_max = Column(DECIMAL(12, 2))
    currency = Column(String(10), default="USD")
    apply_url = Column(Text, nullable=False)
    application_type = Column(Enum(ApplicationType), default=ApplicationType.WEB_FORM)
    ats_platform = Column(Enum(ATSPlatform), default=ATSPlatform.UNKNOWN)
    source = Column(String(100))  # adzuna, jooble, yc, rss
    match_score = Column(Float)  # 0.0 to 1.0
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    applied_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Full-text search vectors
    title_company_tsvector = Column(TSVECTOR)
    description_tsvector = Column(TSVECTOR)

    # Relationships
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("ApplicationLog", back_populates="job", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"))
    cover_letter = Column(Text)
    email_content = Column(Text)
    application_type = Column(Enum(ApplicationType), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True)
    ats_platform = Column(Enum(ATSPlatform))
    submitted_at = Column(DateTime(timezone=True))
    last_attempt_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    model_used = Column(String(100))
    fallback_used = Column(Boolean, default=False)
    success_verified = Column(Boolean, default=False)
    verification_screenshot_path = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job = relationship("Job", back_populates="applications")
    user = relationship("UserProfile", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
    logs = relationship("ApplicationLog", back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        # Unique constraint: one application per job per user
        __import__('sqlalchemy').UniqueConstraint('job_id', 'user_id', name='uq_job_user_application'),
    )


class ApplicationLog(Base):
    __tablename__ = "application_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    action = Column(String(100), nullable=False)  # collected, analyzed, applying, submitted, failed
    status = Column(String(50))
    message = Column(Text)
    error_details = Column(Text)
    model_used = Column(String(100))
    response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    job = relationship("Job", back_populates="logs")
    application = relationship("Application", back_populates="logs")


class ModelUsage(Base):
    __tablename__ = "model_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # groq, openrouter, huggingface
    request_type = Column(String(100))  # job_analysis, form_detection, content_generation
    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    cost_usd = Column(DECIMAL(10, 6))
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    max_daily_applications = Column(Integer, default=20)
    min_match_score = Column(Float, default=0.6)
    auto_approve_high_match = Column(Boolean, default=True)
    preferred_locations = Column(ARRAY(String))
    remote_only = Column(Boolean, default=False)
    excluded_companies = Column(ARRAY(String))
    keywords_include = Column(ARRAY(String))
    keywords_exclude = Column(ARRAY(String))
    notification_email = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("UserProfile", back_populates="preferences")
