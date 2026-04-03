"""
AI Service with multi-model fallback support.
Provides LLM capabilities using Groq, OpenRouter, and HuggingFace with automatic retry logic.
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from httpx import AsyncClient
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class AIFallbackService:
    """
    AI service with automatic fallback between multiple LLM providers.
    Order: Groq (primary) → OpenRouter (fallback 1) → HuggingFace (fallback 2)
    """

    def __init__(self):
        self.groq_client = None
        self.openrouter_client = None
        self.http_client = AsyncClient()
        
        # Initialize Groq if API key available
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = ChatGroq(
                    model=settings.PRIMARY_MODEL,
                    groq_api_key=settings.GROQ_API_KEY,
                    temperature=0.3,
                    max_tokens=2000,
                )
                logger.info("Groq client initialized", model=settings.PRIMARY_MODEL)
            except Exception as e:
                logger.warning("Failed to initialize Groq client", error=str(e))
        
        # Initialize OpenRouter if API key available
        if settings.OPENROUTER_API_KEY:
            try:
                self.openrouter_client = ChatOpenAI(
                    model=settings.FALLBACK_MODEL_1,
                    openai_api_key=settings.OPENROUTER_API_KEY,
                    openai_api_base="https://openrouter.ai/api/v1",
                    temperature=0.3,
                    max_tokens=2000,
                )
                logger.info("OpenRouter client initialized", model=settings.FALLBACK_MODEL_1)
            except Exception as e:
                logger.warning("Failed to initialize OpenRouter client", error=str(e))

    async def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        request_type: str = "general",
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate text with automatic fallback between models.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            request_type: Type of request for logging
            max_retries: Maximum retry attempts per model
            
        Returns:
            Dictionary with response, model_used, fallback_used, tokens, etc.
        """
        models_to_try = []
        
        # Build list of models to try in order
        if self.groq_client:
            models_to_try.append(("groq", self.groq_client, settings.PRIMARY_MODEL))
        if self.openrouter_client:
            models_to_try.append(("openrouter", self.openrouter_client, settings.FALLBACK_MODEL_1))
        
        # Add HuggingFace as last resort (always available via HTTP)
        models_to_try.append(("huggingface", None, settings.FALLBACK_MODEL_2))
        
        last_error = None
        
        for provider, client, model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"Attempting {provider} generation",
                        model=model_name,
                        attempt=attempt + 1,
                        request_type=request_type,
                    )
                    
                    start_time = time.time()
                    
                    if provider == "huggingface":
                        response = await self._generate_huggingface(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            model=model_name,
                        )
                    else:
                        response = await self._generate_langchain(
                            client=client,
                            prompt=prompt,
                            system_prompt=system_prompt,
                            model=model_name,
                        )
                    
                    response_time = int((time.time() - start_time) * 1000)
                    
                    logger.info(
                        f"Successful generation from {provider}",
                        model=model_name,
                        response_time_ms=response_time,
                        request_type=request_type,
                    )
                    
                    return {
                        "success": True,
                        "response": response["content"],
                        "model_used": model_name,
                        "provider": provider,
                        "fallback_used": provider != "groq",
                        "tokens_input": response.get("tokens_input", 0),
                        "tokens_output": response.get("tokens_output", 0),
                        "response_time_ms": response_time,
                        "error": None,
                    }
                    
                except Exception as e:
                    last_error = str(e)
                    logger.warning(
                        f"{provider} generation failed",
                        model=model_name,
                        attempt=attempt + 1,
                        error=last_error,
                    )
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    
        # All models failed
        logger.error("All AI models failed", error=last_error)
        return {
            "success": False,
            "response": None,
            "model_used": None,
            "provider": None,
            "fallback_used": True,
            "tokens_input": 0,
            "tokens_output": 0,
            "response_time_ms": 0,
            "error": last_error,
        }

    async def _generate_langchain(
        self,
        client: Any,
        prompt: str,
        system_prompt: str,
        model: str,
    ) -> Dict[str, Any]:
        """Generate using LangChain client (Groq or OpenRouter)."""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]
        
        response = await client.ainvoke(messages)
        
        return {
            "content": response.content,
            "tokens_input": 0,  # Would need to calculate separately
            "tokens_output": 0,
        }

    async def _generate_huggingface(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
    ) -> Dict[str, Any]:
        """Generate using HuggingFace Inference API."""
        if not settings.HUGGINGFACE_TOKEN:
            raise ValueError("HuggingFace token not configured")
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        
        response = await self.http_client.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {settings.HUGGINGFACE_TOKEN}"},
            json={
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": 2000,
                    "temperature": 0.3,
                    "return_full_text": False,
                }
            },
            timeout=60,
        )
        
        if response.status_code != 200:
            raise Exception(f"HuggingFace API error: {response.status_code}")
        
        result = response.json()
        content = result[0]["generated_text"] if isinstance(result, list) else result["generated_text"]
        
        return {
            "content": content.strip(),
            "tokens_input": 0,
            "tokens_output": 0,
        }

    async def analyze_job_description(
        self,
        job_title: str,
        company: str,
        description: str,
        requirements: str,
    ) -> Dict[str, Any]:
        """Analyze a job description and extract key information."""
        
        system_prompt = """You are an expert job application analyst. 
Your task is to analyze job descriptions and identify:
1. Key skills and qualifications required
2. Company culture indicators
3. ATS platform detection hints (mentions of Lever, Greenhouse, Workday, etc.)
4. Application type (web form, email, LinkedIn)
5. Match score factors

Be precise and factual. Do not hallucinate information."""

        prompt = f"""
Analyze this job posting:

**Position:** {job_title} at {company}

**Description:**
{description[:3000]}  # Truncate if too long

**Requirements:**
{requirements[:2000] if requirements else "Not specified"}

Provide your analysis in JSON format with these fields:
- key_skills: array of top 5-10 required skills
- experience_level: junior/mid/senior/lead
- ats_platform_hint: lever/greenhouse/workday/other/unknown
- application_type: web_form/direct_email/linkedin_easy_apply
- culture_keywords: array of 3-5 culture indicators
- match_factors: array of factors that would indicate good candidate fit
- red_flags: array of any concerning elements
"""

        return await self.generate_with_fallback(
            prompt=prompt,
            system_prompt=system_prompt,
            request_type="job_analysis",
        )

    async def detect_form_fields(
        self,
        page_html: str,
    ) -> Dict[str, Any]:
        """Detect form field selectors from HTML for browser automation."""
        
        system_prompt = """You are an expert web scraping assistant.
Analyze HTML and identify CSS selectors for form fields.
Focus on: name, email, phone, resume upload, cover letter, submit button.
Return ONLY valid JSON with selector mappings."""

        # Truncate HTML to avoid token limits
        truncated_html = page_html[:8000] if len(page_html) > 8000 else page_html
        
        prompt = f"""
Analyze this HTML and find CSS selectors for common application form fields:

{truncated_html}

Return JSON with this structure:
{{
    "name_field": "css_selector_or_null",
    "email_field": "css_selector_or_null",
    "phone_field": "css_selector_or_null",
    "resume_upload": "css_selector_or_null",
    "cover_letter_field": "css_selector_or_null",
    "submit_button": "css_selector_or_null",
    "form_action_url": "url_or_null",
    "additional_fields": [
        {{"label": "field_label", "selector": "css_selector", "type": "text|email|file|textarea"}}
    ],
    "is_multi_page": boolean,
    "next_button": "css_selector_or_null"
}}
"""

        return await self.generate_with_fallback(
            prompt=prompt,
            system_prompt=system_prompt,
            request_type="form_detection",
        )

    async def generate_application_content(
        self,
        job_title: str,
        company: str,
        description: str,
        personal_context: Dict[str, Any],
        content_type: str = "cover_letter",
    ) -> Dict[str, Any]:
        """Generate tailored application content using RAG approach."""
        
        system_prompt = """You are a professional career coach and application writer.
Generate personalized application content based ONLY on the provided personal context.
NEVER fabricate experience, skills, or qualifications.
If the personal context lacks relevant information, acknowledge it honestly.
Be concise, professional, and tailored to the specific role and company."""

        prompt = f"""
Generate a {content_type.replace('_', ' ')} for this position:

**Position:** {job_title} at {company}

**Job Description:**
{description[:2000]}

**My Personal Context:**
{self._format_personal_context(personal_context)}

Requirements:
- Length: 200-300 words
- Highlight relevant experience from my background
- Connect my skills to the job requirements
- Professional but enthusiastic tone
- NO hallucinated information - use ONLY what's in my personal context

Generate the {content_type.replace('_', ' ')}:
"""

        return await self.generate_with_fallback(
            prompt=prompt,
            system_prompt=system_prompt,
            request_type="content_generation",
        )

    def _format_personal_context(self, context: Dict[str, Any]) -> str:
        """Format personal context for the prompt."""
        formatted = []
        
        if "experience" in context:
            exp = context["experience"]
            formatted.append(f"Years of Experience: {exp.get('years', 'N/A')}")
            if "roles" in exp:
                formatted.append("\nWork History:")
                for role in exp.get("roles", [])[:3]:  # Limit to recent 3 roles
                    formatted.append(f"- {role.get('title')} at {role.get('company')} ({role.get('duration')})")
                    if "description" in role:
                        formatted.append(f"  {role['description']}")
        
        if "skills" in context:
            formatted.append(f"\nKey Skills: {', '.join(context['skills'][:15])}")
        
        if "projects" in context:
            formatted.append("\nNotable Projects:")
            for project in context.get("projects", [])[:3]:
                formatted.append(f"- {project.get('name')}: {project.get('description', '')}")
        
        if "education" in context:
            formatted.append("\nEducation:")
            for edu in context.get("education", []):
                formatted.append(f"- {edu.get('degree')} in {edu.get('field')} from {edu.get('institution')}")
        
        return "\n".join(formatted)

    async def close(self):
        """Close HTTP client connections."""
        await self.http_client.aclose()


# Global instance
ai_service = AIFallbackService()


def get_ai_service() -> AIFallbackService:
    """Get the global AI service instance."""
    return ai_service
