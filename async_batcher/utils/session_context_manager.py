# session_context_manager.py

import asyncio
from typing import Dict, Tuple
from playwright.async_api import BrowserContext
import time
import logging

logger = logging.getLogger("session_manager")

class SessionContextManager:
    def __init__(self, max_requests_per_session: int = 10, session_ttl: int = 300):
        self.sessions: Dict[str, Tuple[BrowserContext, int, float]] = {}
        self.max_requests = max_requests_per_session
        self.session_ttl = session_ttl  # seconds
        self.lock = asyncio.Lock()

    async def get_or_create(self, session_key: str, create_context_fn) -> BrowserContext:
        async with self.lock:
            context, count, created_at = self.sessions.get(session_key, (None, 0, 0))
            now = time.time()

            if context and count < self.max_requests and now - created_at < self.session_ttl:
                self.sessions[session_key] = (context, count + 1, created_at)
                logger.debug(f"Reusing context for session {session_key} (count={count + 1})")
                return context

            if context:
                await context.close()
                logger.info(f"Closed expired context for session {session_key}")

            new_context = await create_context_fn()
            self.sessions[session_key] = (new_context, 1, now)
            logger.info(f"Created new context for session {session_key}")
            return new_context

    async def close_all(self):
        async with self.lock:
            for key, (context, _, _) in self.sessions.items():
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"Error closing context for session {key}: {e}")
            self.sessions.clear()
            logger.info("Closed all session contexts")
