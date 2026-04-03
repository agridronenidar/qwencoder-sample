# n8n LoopCV Clone - Setup Guide

## Quick Start

### 1. Prerequisites Installation

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker-compose --version
```

### 2. Environment Setup

```bash
# Navigate to workspace
cd /workspace

# Create required directories (already done)
mkdir -p context workflows templates resumes data

# Place your resume PDF in the resumes folder
cp /path/to/your/resume.pdf ./resumes/resume.pdf
```

### 3. Configure Personal Data

Edit `/workspace/context/personal_data.json` with YOUR actual information:

```json
{
  "personal_info": {
    "full_name": "Your Actual Name",
    "email": "your.real.email@example.com",
    "phone": "+1-555-123-4567",
    ...
  }
}
```

**⚠️ IMPORTANT**: Never commit this file with real data to version control!

### 4. API Keys Setup

You'll need to configure these credentials in n8n:

#### Adzuna API (Free)
1. Register at: https://developer.adzuna.com/
2. Get App ID and App Key
3. In n8n: Credentials → Add Credential → HTTP Request → Enter keys

#### Groq API (Free Tier)
1. Register at: https://console.groq.com/
2. Generate API key
3. In n8n: Credentials → Groq → Enter API key

#### OpenRouter (Optional Fallback)
1. Register at: https://openrouter.ai/
2. Generate API key
3. Add credits (pay-as-you-go)

#### Google Sheets/OAuth
1. In n8n: Credentials → Google Sheets OAuth2
2. Follow OAuth flow to authorize
3. Create a Google Sheet with columns matching `data/excel_schema.json`

### 5. Deploy with Docker

```bash
# Edit docker-compose.yml and change the encryption key
sed -i 's/your-secret-encryption-key-change-me/'$(openssl rand -hex 32)'/' docker-compose.yml

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f n8n
docker-compose logs -f browserless
```

### 6. Import Workflows into n8n

1. Open n8n: http://localhost:5678
2. Go to Workflows → Import from File
3. Import `workflows/scout_workflow.json`
4. Import `workflows/executor_workflow.json`

### 7. Configure Workflow Credentials

For each workflow, update the credential references:

**Scout Workflow:**
- Adzuna API node: Select your Adzuna credentials
- Google Sheets node: Select your Google OAuth credentials
- Set the correct Sheet ID

**Executor Workflow:**
- Groq LLM nodes: Select Groq credentials
- OpenRouter node: Select OpenRouter credentials (if using)
- Browserless HTTP nodes: Update URL if not using default
- Gmail node: Configure OAuth for sending emails
- Google Sheets nodes: Same as Scout workflow

### 8. Create Tracking Spreadsheet

Create a Google Sheet with these columns (or use Excel with Microsoft node):

| ID | Timestamp | Job_Title | Company | Location | Source | Apply_URL | Application_Type | ATS_Platform | Contact_Email | Job_Description | Required_Skills | Match_Score | Status | LLM_Model_Used | Cover_Letter_Generated | Customizations | Error_Log | Date_Processed | Retry_Count |
|----|-----------|-----------|---------|----------|--------|-----------|------------------|--------------|---------------|-----------------|-----------------|-------------|--------|----------------|----------------------|----------------|-----------|----------------|-------------|

### 9. Test the System

#### Test Scout Workflow:
```bash
# Manually trigger in n8n UI
# Should collect jobs and add to spreadsheet
```

#### Test Executor Workflow:
1. Add a test job manually to spreadsheet with Status = "Pending"
2. Trigger executor workflow
3. Monitor browserless logs for automation activity
4. Check spreadsheet for status updates

### 10. Production Considerations

#### Security:
- [ ] Change default encryption key
- [ ] Use environment variables for sensitive data
- [ ] Enable n8n authentication
- [ ] Restrict browserless access to internal network only
- [ ] Never commit personal_data.json with real info

#### Reliability:
- [ ] Set up monitoring/alerting for failed applications
- [ ] Configure retry limits (max 2-3 attempts)
- [ ] Regular backups of tracking spreadsheet
- [ ] Log rotation for browserless and n8n

#### Performance:
- [ ] Adjust schedule frequency based on API rate limits
- [ ] Monitor browserless concurrent session limits
- [ ] Cache frequently accessed personal data
- [ ] Implement deduplication logic for job postings

## Troubleshooting

### Browserless Connection Issues
```bash
# Check if browserless is running
docker ps | grep browserless

# Test connection
curl http://localhost:3000/version

# Check logs
docker logs browserless
```

### n8n Workflow Errors
- Check execution history in n8n UI
- Verify all credentials are properly configured
- Ensure Google Sheet ID is correct
- Check API rate limits (Adzuna: 50 calls/day free tier)

### LLM Fallback Not Triggering
- Verify error handling in "Check Groq Success" node
- Ensure OpenRouter credentials are valid
- Check model availability on respective platforms

## Next Steps

1. **Customize Prompts**: Adjust LLM prompts in workflows for your specific tone/style
2. **Add More Sources**: Integrate YC Startups scraper, RSS feeds
3. **Enhance RAG**: Add vector database for better project matching
4. **Analytics**: Build dashboard for application success rates
5. **A/B Testing**: Test different cover letter approaches

## Support Resources

- n8n Documentation: https://docs.n8n.io/
- Browserless Docs: https://docs.browserless.io/
- Groq API Docs: https://console.groq.com/docs
- Community Forum: https://community.n8n.io/
