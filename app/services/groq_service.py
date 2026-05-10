import time
import asyncio
from typing import Dict, Any
from groq import Groq, RateLimitError
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GroqService:
    """Service for calling GROQ API with proper error handling"""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.max_tokens = settings.GROQ_MAX_TOKENS
        self.temperature = settings.GROQ_TEMPERATURE
        self.timeout = settings.GROQ_TIMEOUT

    async def generate_case(self, prompt: str) -> Dict[str, Any]:
        """
        Call GROQ API to generate case study asynchronously.
        
        GROQ is fast (100-500ms), perfect for case generation.
        Uses asyncio executor to run sync GROQ client in thread pool.
        """
        try:
            start_time = time.time()
            
            # Run sync GROQ call in executor (thread pool)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._call_groq_sync,
                prompt
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "case_generation_success",
                extra={
                    "elapsed_ms": elapsed_ms,
                    "model": self.model,
                    "tokens": response.usage.completion_tokens,
                    "input_tokens": response.usage.prompt_tokens
                }
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "elapsed_ms": elapsed_ms,
                "tokens_used": response.usage.completion_tokens,
                "input_tokens": response.usage.prompt_tokens
            }
        
        except RateLimitError as e:
            logger.warning(
                "groq_rate_limit",
                extra={"error": str(e)}
            )
            # Wait and retry once
            await asyncio.sleep(2)
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self._call_groq_sync,
                    prompt
                )
                elapsed_ms = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "content": response.choices[0].message.content,
                    "elapsed_ms": elapsed_ms,
                    "tokens_used": response.usage.completion_tokens,
                    "input_tokens": response.usage.prompt_tokens
                }
            except Exception as retry_error:
                logger.error(
                    "groq_retry_failed",
                    extra={"error": str(retry_error)}
                )
                return {
                    "success": False,
                    "error": "Rate limit hit and retry failed"
                }
        
        except Exception as e:
            logger.error(
                "groq_api_error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return {
                "success": False,
                "error": str(e)
            }

    def _call_groq_sync(self, prompt: str):
        """Synchronous GROQ API call (runs in thread pool)"""
        return self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )

    async def test_connection(self) -> bool:
        """Test if GROQ API is accessible"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._call_groq_sync,
                "Say 'OK' in one word"
            )
            return response.choices[0].message.content.lower() == "ok"
        except Exception as e:
            logger.error(
                "groq_connection_test_failed",
                extra={"error": str(e)}
            )
            return False