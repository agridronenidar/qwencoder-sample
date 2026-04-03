"""
Database initialization script for PostgreSQL.
Creates necessary extensions and initial schema.
"""

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE application_status AS ENUM (
    'pending',
    'collecting',
    'ready_to_apply',
    'applying',
    'applied',
    'interview_requested',
    'rejected',
    'offer_received',
    'manual_review_required',
    'failed'
);

CREATE TYPE application_type AS ENUM (
    'web_form',
    'direct_email',
    'linkedin_easy_apply',
    'company_portal'
);

CREATE TYPE ats_platform AS ENUM (
    'lever',
    'greenhouse',
    'workday',
    'icims',
    'ashby',
    'other',
    'unknown'
);

-- Log table for audit trail
CREATE TABLE application_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50),
    message TEXT,
    error_details TEXT,
    model_used VARCHAR(100),
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255),
    title VARCHAR(500) NOT NULL,
    company VARCHAR(500) NOT NULL,
    location VARCHAR(500),
    remote_type VARCHAR(100), -- fully_remote, hybrid, onsite
    description TEXT,
    requirements TEXT,
    salary_min DECIMAL(12, 2),
    salary_max DECIMAL(12, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    apply_url TEXT NOT NULL,
    application_type application_type DEFAULT 'web_form',
    ats_platform ats_platform DEFAULT 'unknown',
    source VARCHAR(100), -- adzuna, jooble, yc, rss
    match_score DECIMAL(5, 4), -- 0.0 to 1.0
    status application_status DEFAULT 'pending',
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User profiles (for multi-user support in future)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Resumes
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) DEFAULT 'pdf',
    is_primary BOOLEAN DEFAULT false,
    tags TEXT[], -- e.g., ['embedded', 'aerospace', 'ai']
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Personal data context (for RAG)
CREATE TABLE personal_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    data_key VARCHAR(100) NOT NULL, -- experience, projects, skills, education
    data_value JSONB NOT NULL,
    is_verified BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, data_key)
);

-- Job applications
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id),
    cover_letter TEXT,
    email_content TEXT,
    application_type application_type NOT NULL,
    status application_status DEFAULT 'pending',
    ats_platform ats_platform,
    submitted_at TIMESTAMP WITH TIME ZONE,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    model_used VARCHAR(100),
    fallback_used BOOLEAN DEFAULT false,
    success_verified BOOLEAN DEFAULT false,
    verification_screenshot_path VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, user_id)
);

-- AI model usage tracking
CREATE TABLE model_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL, -- groq, openrouter, huggingface
    request_type VARCHAR(100), -- job_analysis, form_detection, content_generation
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10, 6),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE UNIQUE,
    max_daily_applications INTEGER DEFAULT 20,
    min_match_score DECIMAL(5, 4) DEFAULT 0.6,
    auto_approve_high_match BOOLEAN DEFAULT true,
    preferred_locations TEXT[],
    remote_only BOOLEAN DEFAULT false,
    excluded_companies TEXT[],
    keywords_include TEXT[],
    keywords_exclude TEXT[],
    notification_email BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_match_score ON jobs(match_score DESC);
CREATE INDEX idx_jobs_collected_at ON jobs(collected_at DESC);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_jobs_title_company ON jobs USING gin(to_tsvector('english', title || ' ' || company));
CREATE INDEX idx_jobs_description ON jobs USING gin(to_tsvector('english', description));

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user
INSERT INTO user_profiles (email, full_name) 
VALUES ('admin@autoapply.local', 'Default User');

-- Insert sample personal context
INSERT INTO personal_context (user_id, data_key, data_value) 
SELECT id, 'experience', '{
    "years": 5,
    "roles": [
        {
            "title": "Embedded Systems Engineer",
            "company": "Aerospace Tech Inc",
            "duration": "2020-Present",
            "description": "Developed flight software for CubeSat missions using C++ and Python"
        }
    ],
    "skills": ["C++", "Python", "Embedded Systems", "Flight Software", "Machine Learning"]
}'::jsonb
FROM user_profiles WHERE email = 'admin@autoapply.local';
