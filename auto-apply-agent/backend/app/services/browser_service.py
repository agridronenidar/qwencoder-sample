"""
Browser automation service using Playwright and Browserless.
Handles form filling, resume upload, and application submission.
"""

import asyncio
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Page, Browser
import structlog
import os

from app.config import settings

logger = structlog.get_logger(__name__)


class BrowserAutomationService:
    """
    Service for automating job application forms using Playwright.
    Connects to Browserless.io or local headless Chrome instance.
    """

    def __init__(self):
        self.browserless_url = settings.BROWSERLESS_URL
        self.timeout = settings.PLAYWRIGHT_TIMEOUT
        self.screenshots_dir = settings.SCREENSHOTS_DIR
        
        # Ensure screenshots directory exists
        os.makedirs(self.screenshots_dir, exist_ok=True)

    async def apply_to_job(
        self,
        url: str,
        personal_data: Dict[str, Any],
        resume_path: str,
        form_fields: Optional[Dict[str, str]] = None,
        cover_letter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Automate job application submission.
        
        Args:
            url: Job application page URL
            personal_data: User's personal information
            resume_path: Path to resume PDF
            form_fields: Pre-detected form field selectors (optional)
            cover_letter: Cover letter text (optional)
            
        Returns:
            Application result with success status, screenshot, etc.
        """
        result = {
            "success": False,
            "url": url,
            "screenshot_path": None,
            "error": None,
            "steps_completed": [],
            "final_page_title": None,
            "submission_confirmed": False,
        }
        
        browser = None
        
        try:
            logger.info("Starting browser automation", url=url)
            
            async with async_playwright() as p:
                # Connect to browserless
                ws_url = f"{self.browserless_url}?timeout={self.timeout}"
                browser = await p.chromium.connect(ws_url)
                
                page = await browser.new_page(
                    viewport={"width": 1920, "height": 1080}
                )
                
                # Set timeout
                page.set_default_timeout(self.timeout)
                
                # Navigate to application page
                result["steps_completed"].append("navigating")
                logger.info("Navigating to application page", url=url)
                
                response = await page.goto(url, wait_until="networkidle")
                
                if response and response.status >= 400:
                    raise Exception(f"Page returned status {response.status}")
                
                result["final_page_title"] = await page.title()
                
                # Take initial screenshot
                initial_screenshot = os.path.join(
                    self.screenshots_dir, 
                    f"initial_{url.replace('/', '_')[:50]}.png"
                )
                await page.screenshot(path=initial_screenshot)
                
                # Detect form fields if not provided
                if not form_fields:
                    result["steps_completed"].append("detecting_fields")
                    logger.info("Detecting form fields")
                    form_fields = await self._detect_form_fields(page)
                
                # Fill form fields
                result["steps_completed"].append("filling_form")
                logger.info("Filling application form")
                
                await self._fill_form(
                    page=page,
                    form_fields=form_fields,
                    personal_data=personal_data,
                    resume_path=resume_path,
                    cover_letter=cover_letter,
                )
                
                # Take pre-submit screenshot
                pre_submit_screenshot = os.path.join(
                    self.screenshots_dir,
                    f"pre_submit_{url.replace('/', '_')[:50]}.png"
                )
                await page.screenshot(path=pre_submit_screenshot)
                
                # Submit form
                result["steps_completed"].append("submitting")
                logger.info("Submitting application")
                
                submit_success = await self._submit_form(page, form_fields)
                
                if not submit_success:
                    raise Exception("Failed to submit form - no submit button found or click failed")
                
                # Wait for navigation or confirmation
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except:
                    pass  # Some forms don't navigate after submit
                
                # Take post-submit screenshot
                result["screenshot_path"] = os.path.join(
                    self.screenshots_dir,
                    f"final_{url.replace('/', '_')[:50]}.png"
                )
                await page.screenshot(path=result["screenshot_path"])
                
                # Verify submission
                result["steps_completed"].append("verifying")
                result["submission_confirmed"] = await self._verify_submission(page)
                result["final_page_title"] = await page.title()
                
                if result["submission_confirmed"]:
                    result["success"] = True
                    logger.info("Application submitted successfully", url=url)
                else:
                    logger.warning("Submission verification inconclusive", url=url)
                    result["success"] = True  # Still mark as success if no errors
                
        except Exception as e:
            result["error"] = str(e)
            logger.error("Browser automation failed", url=url, error=str(e))
            
            # Take error screenshot
            if browser:
                try:
                    error_screenshot = os.path.join(
                        self.screenshots_dir,
                        f"error_{url.replace('/', '_')[:50]}.png"
                    )
                    # Would need page context here - simplified for now
                    result["screenshot_path"] = error_screenshot
                except:
                    pass
        
        finally:
            if browser:
                await browser.close()
        
        return result

    async def _detect_form_fields(self, page: Page) -> Dict[str, Any]:
        """Detect form field selectors on the page."""
        # This would typically call the AI service to analyze HTML
        # For now, use common selector patterns
        
        form_fields = {
            "name_field": None,
            "email_field": None,
            "phone_field": None,
            "resume_upload": None,
            "cover_letter_field": None,
            "submit_button": None,
            "additional_fields": [],
        }
        
        # Common selectors for name
        name_selectors = [
            'input[name*="name" i]',
            'input[placeholder*="name" i]',
            '#name',
            'input[type="text"][aria-label*="name" i]',
        ]
        
        for selector in name_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    form_fields["name_field"] = selector
                    break
            except:
                continue
        
        # Common selectors for email
        email_selectors = [
            'input[type="email"]',
            'input[name*="email" i]',
            'input[placeholder*="email" i]',
            '#email',
        ]
        
        for selector in email_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    form_fields["email_field"] = selector
                    break
            except:
                continue
        
        # Common selectors for phone
        phone_selectors = [
            'input[type="tel"]',
            'input[name*="phone" i]',
            'input[placeholder*="phone" i]',
            '#phone',
        ]
        
        for selector in phone_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    form_fields["phone_field"] = selector
                    break
            except:
                continue
        
        # Resume upload
        resume_selectors = [
            'input[type="file"][accept*="pdf"]',
            'input[type="file"][name*="resume" i]',
            'input[type="file"][name*="cv" i]',
            'input[data-testid*="resume"]',
        ]
        
        for selector in resume_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    form_fields["resume_upload"] = selector
                    break
            except:
                continue
        
        # Cover letter
        cover_letter_selectors = [
            'textarea[name*="cover" i]',
            'textarea[placeholder*="cover" i]',
            'textarea[name*="letter" i]',
            '#cover-letter',
            'div[contenteditable="true"]',
        ]
        
        for selector in cover_letter_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    form_fields["cover_letter_field"] = selector
                    break
            except:
                continue
        
        # Submit button
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            '[data-testid*="submit"]',
            '.submit-button',
            '#submit',
        ]
        
        for selector in submit_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    form_fields["submit_button"] = selector
                    break
            except:
                continue
        
        return form_fields

    async def _fill_form(
        self,
        page: Page,
        form_fields: Dict[str, Any],
        personal_data: Dict[str, Any],
        resume_path: str,
        cover_letter: Optional[str] = None,
    ):
        """Fill the application form with provided data."""
        
        # Fill name
        if form_fields.get("name_field"):
            try:
                await page.fill(
                    form_fields["name_field"],
                    personal_data.get("full_name", ""),
                )
            except Exception as e:
                logger.warning("Failed to fill name field", error=str(e))
        
        # Fill email
        if form_fields.get("email_field"):
            try:
                await page.fill(
                    form_fields["email_field"],
                    personal_data.get("email", ""),
                )
            except Exception as e:
                logger.warning("Failed to fill email field", error=str(e))
        
        # Fill phone
        if form_fields.get("phone_field"):
            try:
                await page.fill(
                    form_fields["phone_field"],
                    personal_data.get("phone", ""),
                )
            except Exception as e:
                logger.warning("Failed to fill phone field", error=str(e))
        
        # Upload resume
        if form_fields.get("resume_upload") and os.path.exists(resume_path):
            try:
                await page.set_input_files(
                    form_fields["resume_upload"],
                    resume_path,
                )
                logger.info("Resume uploaded successfully")
            except Exception as e:
                logger.error("Failed to upload resume", error=str(e))
                raise
        
        # Fill cover letter
        if form_fields.get("cover_letter_field") and cover_letter:
            try:
                await page.fill(
                    form_fields["cover_letter_field"],
                    cover_letter,
                )
            except Exception as e:
                logger.warning("Failed to fill cover letter", error=str(e))

    async def _submit_form(
        self,
        page: Page,
        form_fields: Dict[str, Any],
    ) -> bool:
        """Submit the form by clicking the submit button."""
        
        if not form_fields.get("submit_button"):
            return False
        
        try:
            await page.click(form_fields["submit_button"])
            return True
        except Exception as e:
            logger.warning("Failed to click submit button", error=str(e))
            return False

    async def _verify_submission(self, page: Page) -> bool:
        """Verify that the application was successfully submitted."""
        
        # Look for common success indicators
        success_indicators = [
            "thank you",
            "application submitted",
            "confirmation",
            "successfully",
            "we've received",
            "next steps",
        ]
        
        try:
            page_content = await page.content()
            page_text = page_content.lower()
            
            for indicator in success_indicators:
                if indicator in page_text:
                    logger.info("Found submission confirmation", indicator=indicator)
                    return True
            
            # Check URL changes (some ATS redirect to thank you page)
            current_url = page.url
            if "thank" in current_url.lower() or "confirmation" in current_url.lower():
                return True
            
        except Exception as e:
            logger.warning("Error during submission verification", error=str(e))
        
        return False


# Global instance
browser_service = BrowserAutomationService()


def get_browser_service() -> BrowserAutomationService:
    """Get the global browser automation service instance."""
    return browser_service
