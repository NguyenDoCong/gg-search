# tor_fingerprint_manager.py
import requests
import json
from proxy.fingerprint_generator import CustomFingerprintGenerator
# from playwright.async_api import async_playwright
from stem.control import Controller
from stem import Signal
import logging
import asyncio
import random
import threading
from collections import deque

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
        # self.context_pool = {}  # <--- Thêm pool context theo IP
        # self.browser_pool = {} 
        # self.proxy_ports = [9050, 9052, 9054, 9056, 9058, 9060, 9062, 9064, 9066, 9068]

        self.proxy_ports_available = deque([9050, 9052, 9054, 9056, 9058, 9060, 9062, 9064, 9066, 9068])
        random.shuffle(self.proxy_ports_available) # Trộn ngẫu nhiên để chia đều hơn khi khởi đầu

        # Sử dụng Lock cho các môi trường đa luồng (threading)
        self.port_lock = threading.Lock()
        # Hoặc asyncio.Semaphore cho môi trường asyncio (nếu bạn sử dụng async/await)
        # self.port_semaphore = asyncio.Semaphore(len(self.proxy_ports_available))

        self.current_session = None
        self.password = password

        # Ghi lại port đang được sử dụng bởi session hiện tại để xoay IP đúng
        self.current_proxy_port = None
        self.current_control_port = None

    def get_available_port(self):
        with self.port_lock: # Đảm bảo chỉ một luồng có thể truy cập Queue tại một thời điểm
            if not self.proxy_ports_available:
                logger.error("Không còn proxy port nào khả dụng!")
                raise Exception("No available proxy ports.")
            port = self.proxy_ports_available.popleft() # Lấy một port từ đầu hàng đợi
            # Đưa port này về cuối hàng đợi để sử dụng lại sau này (Round-robin)
            self.proxy_ports_available.append(port)
            logger.info(f"Port được cấp phát: {port}")
            return port

                
    def rotate_ip(self, control_port):
        import time
        max_retries = 5
        
        # Đảm bảo control_port là của instance Tor mà bạn đang xoay
        control_port_to_rotate = self.current_control_port 
        if control_port_to_rotate is None:
            # Nếu chưa có session nào, hoặc đây là lần xoay đầu tiên của một instance
            # có thể cần một cách khác để xác định control_port
            # Hiện tại, giả định rotate_ip luôn được gọi sau khi có session và port được gán
            logger.warning("rotate_ip được gọi khi current_control_port là None. Có thể gây lỗi.")
            return
        
        # if not control_port:
        #     control_port = self.control_port
        for attempt in range(max_retries + 1):
            try:
                with Controller.from_port(port=control_port_to_rotate) as controller:
                
                # with Controller.from_port(port=control_port) as controller:
                    # logger.info("🔄 Đã kết nối tới Tor control port")

                    controller.authenticate(password=self.password or "1")
                    controller.signal(Signal.NEWNYM)
                    time.sleep(5)

                    logger.info(f"✅ Tor IP rotated for control port {control_port_to_rotate}.")
                    return  # success
            except Exception as e:
                logger.warning(f"❌ Lỗi khi xoay IP (attempt {attempt + 1}/{max_retries}): {e}")
                asyncio.sleep(2)  # Thêm delay
                
                if attempt == max_retries:
                    logger.warning("🚫 Max retries reached. Không thể xoay IP.", exc_info=True)
                    
            
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

    def get_new_session(self, proxy_port, control_port):
        import time
        
        try:
            proxy_port = self.get_available_port()
            control_port = proxy_port + 1
        except Exception as e:
            logger.error(f"Không thể lấy port khả dụng: {e}")
            return None # Hoặc raise một ngoại lệ
        
        # control_port = proxy_port + 1                    
            
        # if not proxy_port:            
        #     proxy_port = self.proxy_port            
            
        try:
            self.rotate_ip(control_port)
        except Exception as e:
            logger.error(f"Lỗi xoay IP trên port {control_port}: {e}")
        
        # Wait for new IP to apply
        new_ip = None
        for _ in range(10):
            try:
                tor_ip = requests.get("https://ipinfo.io/json", proxies={
                    "http": f"socks5h://127.0.0.1:{proxy_port}",
                    "https": f"socks5h://127.0.0.1:{proxy_port}"
                }, timeout=5).json()
                new_ip = tor_ip.get("ip")
                if new_ip and new_ip != getattr(self, "last_known_ip", None):
                    break
            except Exception as e:
                pass
            time.sleep(1)

        if not new_ip:
            logger.warning(f"Không thể xác định IP mới từ proxy_port {proxy_port}")
            new_ip = "unknown"
    
        self.last_known_ip = new_ip        
            
        # ip_address = tor_ip.get("ip", "unknown")
        
        # print(f"IP từ proxy_port {proxy_port} và ControlPort {control_port} là {ip_address}")
        # logger.info(f"IP từ proxy_port {proxy_port} và ControlPort {control_port} là {ip_address}")
        
        # self.load_session_pool(domain=domain)
        
        # # logger.info(f"Số lượng session hiện có: {len(self.session_pool)}")

        # # Nếu IP đã tồn tại trong session_pool → dùng lại
        # existing = self.get_session_by_ip(ip_address)
        # if existing:
        #     print("♻️ Reusing existing session for IP:", str(ip_address))
        #     logger.info(f"♻️ Reusing existing session for IP: {ip_address}")
            
        #     self.current_session = existing
        #     return existing
        locale = "en-US"
        timezone_id = "Europe/London"

        fingerprint_data = self.generator.generate_fingerprint(locale=locale)
        fingerprint = fingerprint_data["fingerprint"]
        # fingerprint["locale"] = locale
        # fingerprint["timezone_id"] = timezone_id

        ip_info = {
            # "ip": tor_ip.get("ip", "unknown"),
            "ip": new_ip, 
            "port": str(proxy_port),
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
                "server": f"socks5://127.0.0.1:{proxy_port}"
            },
            "fingerprint": fingerprint,
            "google_domain": fingerprint_data["google_domain"],
            "retry_count": 0
        }
        
        # session["used_count"] = 0  # đếm số lần session này được sử dụng

        # self.session_pool.append(session)
        # self.current_session = session
        # self.save_session_pool(domain=domain)
        return session
    
    # def save_session_pool(self, path="luxirty_sessions.json", domain="luxirty"):
    #     if domain == "luxirty":
    #         path="luxirty_sessions.json"
    #     else:
    #         path="google_sessions.json"  
                      
    #     with open(path, "w", encoding="utf-8") as f:
    #         json.dump(self.session_pool, f, indent=2)

    # def load_session_pool(self, path="luxirty_sessions.json", domain="luxirty"):
        # if domain == "luxirty":
        #     path="luxirty_sessions.json"
        # else:
        #     path="google_sessions.json" 
            
        # try:
        #     with open(path, "r", encoding="utf-8") as f:
        #         self.session_pool = json.load(f)
        #     if self.session_pool:
        #         self.current_session = self.session_pool[-1]
        # except Exception as e:
        #     print("❌ Không thể load session_pool:", e)


    def get_current_session(self, proxy_port=None, control_port=None):
        if self.current_session is None:
            return self.get_new_session(proxy_port=proxy_port, control_port= control_port)
        
        # self.current_session["used_count"] += 1
        # if self.current_session["used_count"] >= 100:
        #     logger.info("🔁 Session đã dùng đủ 100 lần – tạo session mới.")
        #     return self.get_new_session()
                
        return self.current_session

    def rotate_session_if_needed(self, was_blocked=False, max_retries=3):
        if not was_blocked and self.current_session["retry_count"] < max_retries:
            self.current_session["retry_count"] += 1
            return self.current_session
        return self.get_new_session()

    async def setup_browser_context(self, playwright, headless=True, proxy_port=None, control_port=None):
        try:
            # proxy_port = self.get_next_port()
            session = self.get_new_session(proxy_port=proxy_port, control_port= control_port)
        except Exception as e:
            print("Lỗi tạo session mới", e)
            return None
        

        # ip = session["proxy"]["ip"]       
        
        # Nếu đã có browser/context cho IP này thì dùng lại
        # if ip in self.context_pool and ip in self.browser_pool:
        #     context = self.context_pool[ip]
        #     browser = self.browser_pool[ip]
        #     logger.info(f"♻️ Reusing browser/context for IP: {ip}")
        #     return context, session
        
        # browser = await playwright.chromium.launch(
        #     headless=headless,
        #     proxy=session["proxy_playwright"]
        # )

        # fingerprint = session["fingerprint"]
        # context = await playwright.new_context(
        #     locale=fingerprint["locale"],
        #     timezone_id=fingerprint["timezone_id"],
        #     color_scheme=fingerprint["color_scheme"],
        #     reduced_motion=fingerprint["reduced_motion"],
        #     forced_colors=fingerprint["forced_colors"]
        # )
        # self.context_pool[ip] = context
        # self.browser_pool[ip] = browser
        # logger.info(f"Khởi tạo browser/context mới cho IP: {ip}")
       
        return session

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

