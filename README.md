# n8n LoopCV Clone - Automated Job Application System

## Overview
A personal automated job application system built on n8n that collects jobs, applies using RAG-based personal data, and tracks application status.

## Architecture

### Module A: The Scout (Collection)
- **Sources**: Adzuna API, Jooble API, YC Startups, RSS Feeds
- **Filtering**: Prioritizes direct apply links (Lever, Greenhouse, Workday)
- **Output**: Excel sheet with pending applications

### Module B: The Brain (RAG + LLM)
- **Knowledge Base**: Resume, GitHub projects, LinkedIn experience
- **LLM Providers**: Groq (primary), OpenRouter (fallback 1), HuggingFace (fallback 2)
- **Zero-Hallucination**: Only uses verified personal experience data

### Module C: The Executor (Application)
- **Direct Email**: Gmail/SMTP node for email applications
- **Headless Browser**: Browserless/Playwright for web form automation
- **Verification**: Confirms successful submission before updating status

### Module D: The Auditor (Tracking)
- Updates Excel status: Pending → Applied / Manual Review Required
- Error logging for failed attempts

## Prerequisites

### Software
- n8n (self-hosted recommended)
- Docker (for local browserless)
- Node.js 18+

### API Keys Required
- Adzuna API (free tier available)
- Groq API key (free tier)
- OpenRouter API key (optional fallback)
- Google OAuth or SMTP credentials (for email applications)

### Services
- Browserless.io account OR local Docker container running browserless/chrome
- Google Sheets or local Excel file access

## Project Structure

```
/workspace
├── README.md                 # This file
├── context/
│   └── personal_data.json    # Your resume, projects, skills data
├── workflows/
│   ├── scout_workflow.json   # Job collection workflow
│   ├── executor_workflow.json # Application workflow
│   └── fallback_logic.json   # Model fallback configuration
├── templates/
│   ├── cover_letter.txt      # Cover letter template
│   └── email_template.txt    # Direct email template
├── resumes/
│   └── resume.pdf            # Your resume file
└── data/
    └── applications.xlsx     # Tracking spreadsheet
```

## Implementation Steps

1. **Setup Phase**
   - Create personal_data.json with your experience
   - Configure n8n credentials
   - Set up browserless container

2. **Build Scout Workflow**
   - Configure API nodes for job sources
   - Add filtering logic
   - Connect to Excel output

3. **Build Executor Workflow**
   - Implement RAG data retrieval
   - Configure LLM nodes with fallback
   - Set up browser automation

4. **Testing & Refinement**
   - Test with sample job postings
   - Verify zero-hallucination constraint
   - Tune fallback thresholds

## Security Notes
- Store API keys in n8n credentials (not in workflow files)
- Never commit personal_data.json with real information
- Use environment variables for sensitive data