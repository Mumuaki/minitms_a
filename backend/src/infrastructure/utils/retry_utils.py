import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class IntegrationError(Exception):
    """Base exception for external integrations."""
    pass

class TransientError(IntegrationError):
    """Temporary failure (e.g. timeout). Should be retried."""
    pass

class RateLimitError(IntegrationError):
    """Rate limit exceeded. Should be retried with longer backoff."""
    pass

class AuthError(IntegrationError):
    """Authentication failure. Usually requires manual or specific re-login."""
    pass

class PermanentError(IntegrationError):
    """Permanent failure. Should not be retried."""
    pass

def async_retry(max_retries=3, backoff_factor=2):
    """
    Декоратор для повторных попыток выполнения асинхронной функции
    при возникновении TransientError или RateLimitError.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except TransientError as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}. Error: {e}")
                        raise PermanentError(f"Failed after {max_retries} retries: {e}") from e
                    
                    sleep_time = backoff_factor ** retries
                        
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} in {sleep_time}s due to: {e}")
                    await asyncio.sleep(sleep_time)
        return wrapper
    return decorator
