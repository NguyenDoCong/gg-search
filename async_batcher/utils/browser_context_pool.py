# browser_context_pool.py

import asyncio
from typing import Tuple, Dict, List
from playwright.async_api import async_playwright, Browser, BrowserContext
import random
import logging

logger = logging.getLogger("browser_pool")

MAX_CONTEXT_PER_BROWSER = 5  # Recommended for Tor or CAPTCHA-prone sites
MAX_TOTAL_BROWSERS = 3       # Limit to avoid memory explosion

class BrowserContextPool:
    def __init__(self):
        self.playwright = None
        self.browsers: List[Browser] = []
        self.browser_contexts: Dict[Browser, List[BrowserContext]] = {}
        self.lock = asyncio.Lock()

    async def start_playwright(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()

    async def new_browser(self) -> Browser:
        browser = await self.playwright.chromium.launch(headless=True)
        self.browsers.append(browser)
        self.browser_contexts[browser] = []
        logger.info(f"Launched new browser. Total browsers: {len(self.browsers)}")
        return browser

    async def get_context(self, **context_options) -> Tuple[str, BrowserContext]:
        async with self.lock:
            await self._start_playwright()

            for browser in self.browsers:
                if len(self.browser_contexts[browser]) < MAX_CONTEXT_PER_BROWSER:
                    context = await browser.new_context(**context_options)
                    self.browser_contexts[browser].append(context)
                    key = f"browser-{id(browser)}-ctx-{id(context)}"
                    logger.debug(f"Created new context in existing browser: {key}")
                    return key, context

            if len(self.browsers) < MAX_TOTAL_BROWSERS:
                browser = await self._new_browser()
                context = await browser.new_context(**context_options)
                self.browser_contexts[browser].append(context)
                key = f"browser-{id(browser)}-ctx-{id(context)}"
                return key, context

            browser = random.choice(self.browsers)
            context = await browser.new_context(**context_options)
            self.browser_contexts[browser].append(context)
            key = f"browser-{id(browser)}-ctx-{id(context)}"
            logger.warning("⚠️ Context pool full — exceeding max limits")
            return key, context

    async def close_all(self):
        for browser in self.browsers:
            await browser.close()
        self.browsers = []
        self.browser_contexts.clear()
        logger.info("Closed all browsers and contexts")

    async def release_context(self, context: BrowserContext):
        for browser, contexts in self.browser_contexts.items():
            if context in contexts:
                try:
                    await context.close()
                    contexts.remove(context)
                    logger.debug("Context closed and removed from pool")
                except Exception as e:
                    logger.warning(f"Failed to close context: {e}")
                return
        logger.warning("Attempted to release context not found in pool")
