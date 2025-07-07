# tor_fingerprint_manager.py
import requests
import json
from utils import CustomFingerprintGenerator
# from playwright.async_api import async_playwright
from stem.control import Controller
from stem import Signal
import logging
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TorFingerprintManager:
    def __init__(self, proxy_port=9050, control_port=9051, password=None):
        self.generator = CustomFingerprintGenerator()
        self.session_pool = []
        self.context_pool = {}  # <--- Thêm pool context theo IP
        self.browser_pool = {} 
        self.current_session = None
        self.proxy_port = proxy_port
        self.control_port = control_port
        self.password = password

    def mark_ip_used(self, ip):
        session = self.get_session_by_ip(ip)
        if session:
            session["used_count"] = session.get("used_count", 0) + 1
            if session["used_count"] >= 20:  
                self.rotate_ip()
                
    def rotate_ip(self, current_retry:int =0):
        max_retries = 5
        for attempt in range(max_retries + 1):
            try:
                with Controller.from_port(port=self.control_port) as controller:
                    # logger.info("🔄 Đã kết nối tới Tor control port")

                    controller.authenticate(password=self.password or "1")
                    controller.signal(Signal.NEWNYM)

                    logger.info("✅ Tor IP rotated.")
                    return  # success
            except Exception as e:
                logger.warning(f"❌ Lỗi khi xoay IP (attempt {attempt + 1}/{max_retries}): {e}")
                asyncio.sleep(2)  # Thêm delay
                
                if attempt == max_retries:
                    logger.error("🚫 Max retries reached. Không thể xoay IP.", exc_info=True)
            
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

    def get_new_session(self, domain, current_retry: int = 0):
        try: 
            self.rotate_ip()  # 🔄 Đổi IP mỗi lần tạo session mới
        except Exception as e:
            print("Lỗi xoay ip:", e)

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
            
        # ip_address = tor_ip.get("ip", "unknown")
        
        # self.load_session_pool(domain=domain)
        
        # # logger.info(f"Số lượng session hiện có: {len(self.session_pool)}")

        # # Nếu IP đã tồn tại trong session_pool → dùng lại
        # existing = self.get_session_by_ip(ip_address)
        # if existing:
        #     print("♻️ Reusing existing session for IP:", str(ip_address))
        #     logger.info(f"♻️ Reusing existing session for IP: {ip_address}")
            
        #     self.current_session = existing
        #     return existing

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
        self.save_session_pool(domain=domain)
        return session
    
    def save_session_pool(self, path="luxirty_sessions.json", domain="luxirty"):
        if domain == "luxirty":
            path="luxirty_sessions.json"
        else:
            path="google_sessions.json"  
                      
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.session_pool, f, indent=2)

    def load_session_pool(self, path="luxirty_sessions.json", domain="luxirty"):
        if domain == "luxirty":
            path="luxirty_sessions.json"
        else:
            path="google_sessions.json" 
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.session_pool = json.load(f)
            if self.session_pool:
                self.current_session = self.session_pool[-1]
        except Exception as e:
            print("❌ Không thể load session_pool:", e)


    def get_current_session(self, domain):
        if self.current_session is None:
            return self.get_new_session(domain=domain)
        return self.current_session

    def rotate_session_if_needed(self, was_blocked=False, max_retries=3):
        if not was_blocked and self.current_session["retry_count"] < max_retries:
            self.current_session["retry_count"] += 1
            return self.current_session
        return self.get_new_session()

    async def setup_browser_context(self, playwright, headless=True, domain="luxirty"):
        try:
            session = self.get_new_session(domain=domain)
        except Exception as e:
            print("Lỗi tạo session mới", e)
            return None, None

        # ip = session["proxy"]["ip"]       
        
        # Nếu đã có browser/context cho IP này thì dùng lại
        # if ip in self.context_pool and ip in self.browser_pool:
        #     context = self.context_pool[ip]
        #     browser = self.browser_pool[ip]
        #     logger.info(f"♻️ Reusing browser/context for IP: {ip}")
        #     return context, session
        
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
        # self.context_pool[ip] = context
        # self.browser_pool[ip] = browser
        # logger.info(f"Khởi tạo browser/context mới cho IP: {ip}")
       
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

