# tor_fingerprint_manager.py
import requests
import json
from utils import CustomFingerprintGenerator
from playwright.async_api import async_playwright
from stem.control import Controller
from stem import Signal
from logging import Logger

class TorFingerprintManager:
    def __init__(self, proxy_port=9050, control_port=9051, password=None):
        self.generator = CustomFingerprintGenerator()
        self.session_pool = []
        self.current_session = None
        self.proxy_port = proxy_port
        self.control_port = control_port
        self.password = password

    def rotate_ip(self):
        with Controller.from_port(port=self.control_port) as controller:
            if self.password:
                controller.authenticate(password=self.password)
            else:
                controller.authenticate(password="1")
            controller.signal(Signal.NEWNYM)
            print("✅ Tor IP rotated.")
            
    def get_session_by_ip(self, ip):
        print(f"Checking IP {ip} in session pool")
        try:
            # print("Looping through session_pool", len(self.session_pool))
            for session in self.session_pool:
                # print("Checking...")
                if session["proxy"].get("ip") == ip:
                    print("IP found in session pool")
                    return session
                # else:
            print("IP not found in session pool. Creating new session")
        except Exception as e:
            print("Failed to loop through session_pool", e)
        return None                

    def get_new_session(self):
        try: 
            self.rotate_ip()  # 🔄 Đổi IP mỗi lần tạo session mới
        except Exception as e:
            print(f"Lỗi xoay ip:", str(e))

        locale = "en-US"
        timezone_id = "Europe/London"

        fingerprint_data = self.generator.generate_fingerprint(locale=locale)
        fingerprint = fingerprint_data["fingerprint"]
        fingerprint["locale"] = locale
        fingerprint["timezone_id"] = timezone_id
        
        # Detect external IP info
        try:
            tor_ip = requests.get("https://ipinfo.io/json", proxies={
                "http": f"socks5h://127.0.0.1:{self.proxy_port}",
                "https": f"socks5h://127.0.0.1:{self.proxy_port}"
            }, timeout=10).json()
        except Exception as e:
            print("[!] Failed to fetch Tor IP info:", e)
            tor_ip = {}
            
        ip_address = tor_ip.get("ip", "unknown")
        
        self.load_session_pool()

        # Nếu IP đã tồn tại trong session_pool → dùng lại
        existing = self.get_session_by_ip(ip_address)
        if existing:
            print("♻️ Reusing existing session for IP:", ip_address)
            Logger.info("♻️ Reusing existing session for IP:", ip_address)
            
            self.current_session = existing
            return existing

        ip_info = {
            "ip": tor_ip.get("ip", "unknown"),
            "port": str(self.proxy_port),
            "user": None,
            "pass": None,
            "locale": locale,
            "timezone_id": timezone_id,
            "city": tor_ip.get("city", "unknown"),
            "country": tor_ip.get("country", "unknown")
        }

        session = {
            "proxy": ip_info,
            "proxy_playwright": {
                "server": f"socks5://127.0.0.1:{self.proxy_port}"
            },
            "fingerprint": fingerprint,
            "google_domain": fingerprint_data["google_domain"],
            "retry_count": 0
        }
        self.session_pool.append(session)
        self.current_session = session
        self.save_session_pool()
        return session
    
    def save_session_pool(self, path="tor_sessions.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.session_pool, f, indent=2)

    def load_session_pool(self, path="tor_sessions.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.session_pool = json.load(f)
            if self.session_pool:
                self.current_session = self.session_pool[-1]
        except Exception as e:
            print("❌ Không thể load session_pool:", e)


    def get_current_session(self):
        if self.current_session is None:
            return self.get_new_session()
        return self.current_session

    def rotate_session_if_needed(self, was_blocked=False, max_retries=3):
        if not was_blocked and self.current_session["retry_count"] < max_retries:
            self.current_session["retry_count"] += 1
            return self.current_session
        return self.get_new_session()

    async def setup_browser_context(self, playwright, headless=True):
        try:
            session = self.get_new_session()
        except Exception as e:
            print("Lỗi tạo session mới", e)
        browser = await playwright.chromium.launch(
            headless=headless,
            proxy=session["proxy_playwright"]
        )

        fingerprint = session["fingerprint"]
        context = await browser.new_context(
            locale=fingerprint["locale"],
            timezone_id=fingerprint["timezone_id"],
            color_scheme=fingerprint["color_scheme"],
            reduced_motion=fingerprint["reduced_motion"],
            forced_colors=fingerprint["forced_colors"]
        )
        return context, session

if __name__ == "__main__":
    manager = TorFingerprintManager()
    session = manager.get_current_session()
    print("Current Session:")
    # print(json.dumps(session, indent=2))
    print(session['proxy']['ip'])
    session_pool = manager.session_pool
    # print(repr(manager.session_pool))
    for session in session_pool:
        # print(json.dumps(session, indent=2))
        print(session['proxy']['ip'])

