# proxy_fingerprint_manager.py

import random
from proxy_helper import PROXIES, proxy_to_playwright_format
from proxy.fingerprint_generator import CustomFingerprintGenerator

class ProxyFingerprintManager:
    def __init__(self):
        self.generator = CustomFingerprintGenerator()
        self.session_pool = []  # Cache các phiên đã khởi tạo
        self.current_session = None

    def get_random_session(self):

        proxy = random.choice(PROXIES)
        # print("proxy in use:", proxy)
        locale = proxy["locale"]
        timezone_id = proxy["timezone_id"]

        fingerprint_data = self.generator.generate_fingerprint(locale=locale)
        fingerprint = fingerprint_data["fingerprint"]
        fingerprint["locale"] = locale
        fingerprint["timezone_id"] = timezone_id

        session = {
            "proxy": proxy,
            "proxy_playwright": proxy_to_playwright_format(proxy),
            "fingerprint": fingerprint,
            "google_domain": fingerprint_data["google_domain"],
            "retry_count": 0,
        }
        self.session_pool.append(session)
        self.current_session = session
        return session

    def get_current_session(self):
        if self.current_session is None:
            return self.get_random_session()
        return self.current_session

    def rotate_session_if_needed(self, was_blocked=False, max_retries=3):
        if not was_blocked and self.current_session["retry_count"] < max_retries:
            self.current_session["retry_count"] += 1
            return self.current_session

        # Nếu bị block hoặc vượt quá retry cho phép => tạo mới
        return self.get_random_session()

    def reset_retry_count(self):
        if self.current_session:
            self.current_session["retry_count"] = 0

    async def setup_browser_context(self, playwright, headless=True):
        session = self.get_current_session()
        browser = await playwright.chromium.launch(
            headless=headless,
            proxy=session["proxy_playwright"]
        )

        context = await browser.new_context(
            locale=session["fingerprint"]["locale"],
            timezone_id=session["fingerprint"]["timezone_id"],
            color_scheme=session["fingerprint"]["color_scheme"],
            reduced_motion=session["fingerprint"]["reduced_motion"],
            forced_colors=session["fingerprint"]["forced_colors"],

        )

        return context, session
    
if __name__ == "__main__":
    # Ví dụ sử dụng
    import json
    manager = ProxyFingerprintManager()
    session = manager.get_current_session()
    pretty_json_string = json.dumps(session, indent=4)

    print("Current Session:", pretty_json_string)
    
    # Lấy context với Playwright (giả sử đã khởi tạo playwright)
    # context, session = await manager.setup_browser_context(playwright)
    # print("Browser Context:", context)    
