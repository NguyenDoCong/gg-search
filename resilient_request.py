# resilient_request.py

import asyncio
import logging

logger = logging.getLogger("resilient")

async def resilient_request(searcher, query, domain=None, max_retries=3):
    """
    Gửi request với khả năng tự xoay session nếu gặp CAPTCHA hoặc lỗi, không ảnh hưởng tới các luồng khác.
    """
    for attempt in range(1, max_retries + 1):
        session = searcher.session_manager.get_current_session(domain)
        try:
            resp = await searcher.get_html(query, save_to_file=False, domain=domain)
            page = await resp["page"] if isinstance(resp, dict) else None

            if page and await searcher.check_captcha_or_sorry(page):
                logger.warning(f"[{attempt}] CAPTCHA detected – rotating session...")
                searcher.session_manager.rotate_session_if_needed(was_blocked=True)
                continue

            return resp

        except Exception as e:
            logger.error(f"[{attempt}] Error in request: {e}")
            searcher.session_manager.rotate_session_if_needed(was_blocked=True)

        await asyncio.sleep(1)

    logger.error("❌ Max retries reached – returning None")
    return None
