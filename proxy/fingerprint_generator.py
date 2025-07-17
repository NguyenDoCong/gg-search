import random
import json
from typing import Dict, List, Optional
from datetime import datetime

class CustomFingerprintGenerator:
    """
    Generator để tạo fingerprints theo định dạng custom
    Format: device_name, locale, timezone_id, color_scheme, reduced_motion, forced_colors
    """

    def __init__(self):
        # Device configurations
        self.devices = {
            "desktop": {
                "browsers": ["Chrome", "Firefox", "Safari", "Edge", "Opera"],
                "os": ["Windows", "MacOS", "Linux"],
            },
            "mobile": {
                "browsers": [
                    "Chrome Mobile",
                    "Safari Mobile",
                    "Firefox Mobile",
                    "Samsung Browser",
                    "Opera Mobile",
                ],
                "os": ["Android", "iOS"],
            },
            "tablet": {
                "browsers": [
                    "Chrome Tablet",
                    "Safari Tablet",
                    "Firefox Tablet",
                    "Edge Tablet",
                ],
                "os": ["Android", "iOS", "Windows"],
            },
        }

        # Locale configurations với trọng số
        self.locales = {
            "vi-VN": 0.15,  # Vietnam
            "en-US": 0.20,  # United States
            "en-GB": 0.10,  # United Kingdom
            "zh-CN": 0.15,  # China
            "ja-JP": 0.08,  # Japan
            "ko-KR": 0.05,  # South Korea
            "fr-FR": 0.05,  # France
            "de-DE": 0.05,  # Germany
            "es-ES": 0.04,  # Spain
            "it-IT": 0.03,  # Italy
            "pt-BR": 0.03,  # Brazil
            "ru-RU": 0.03,  # Russia
            "ar-SA": 0.02,  # Saudi Arabia
            "th-TH": 0.02,  # Thailand
        }

        # Timezone mapping với locale
        self.timezone_mapping = {
            "vi-VN": ["Asia/Ho_Chi_Minh", "Asia/Bangkok", "Asia/Jakarta"],
            "en-US": [
                "America/New_York",
                "America/Chicago",
                "America/Denver",
                "America/Los_Angeles",
                "America/Phoenix",
            ],
            "en-GB": ["Europe/London", "Europe/Dublin"],
            "zh-CN": ["Asia/Shanghai"],
            "ja-JP": ["Asia/Tokyo"],
            "ko-KR": ["Asia/Seoul"],
            "fr-FR": ["Europe/Paris"],
            "de-DE": ["Europe/Berlin"],
            "es-ES": ["Europe/Madrid"],
            "it-IT": ["Europe/Rome"],
            "pt-BR": ["America/Sao_Paulo"],
            "ru-RU": ["Europe/Moscow", "Asia/Yekaterinburg", "Asia/Novosibirsk"],
            "ar-SA": ["Asia/Riyadh"],
            "th-TH": ["Asia/Bangkok"],
        }

        # Google domains theo locale/region
        self.google_domains = {
            "vi-VN": ["https://www.google.com.vn", "https://www.google.com"],
            "en-US": ["https://www.google.com", "https://www.google.us"],
            "en-GB": ["https://www.google.co.uk", "https://www.google.com"],
            "zh-CN": ["https://www.google.com.hk", "https://www.google.com"],
            "ja-JP": ["https://www.google.co.jp", "https://www.google.com"],
            "ko-KR": ["https://www.google.co.kr", "https://www.google.com"],
            "fr-FR": ["https://www.google.fr", "https://www.google.com"],
            "de-DE": ["https://www.google.de", "https://www.google.com"],
            "es-ES": ["https://www.google.es", "https://www.google.com"],
            "it-IT": ["https://www.google.it", "https://www.google.com"],
            "pt-BR": ["https://www.google.com.br", "https://www.google.com"],
            "ru-RU": ["https://www.google.ru", "https://www.google.com"],
            "ar-SA": ["https://www.google.com.sa", "https://www.google.com"],
            "th-TH": ["https://www.google.co.th", "https://www.google.com"],
        }

        # Additional Google domains
        self.additional_google_domains = [
            "https://www.google.com.au",  # Australia
            "https://www.google.ca",  # Canada
            "https://www.google.co.in",  # India
            "https://www.google.com.sg",  # Singapore
            "https://www.google.co.za",  # South Africa
            "https://www.google.com.mx",  # Mexico
            "https://www.google.nl",  # Netherlands
            "https://www.google.se",  # Sweden
            "https://www.google.no",  # Norway
            "https://www.google.dk",  # Denmark
        ]

        # Display preferences
        # self.color_schemes = ["light", "dark", "no-preference"]
        self.color_schemes = ["light", "light", "light"]        
        self.reduced_motions = ["no-preference", "reduce"]
        self.forced_colors = ["none", "active"]

        # Color scheme weights (light is more common)
        self.color_scheme_weights = [0.65, 0.30, 0.05]  # light, dark, no-preference

        # Reduced motion weights (most users don't reduce motion)
        self.reduced_motion_weights = [0.85, 0.15]  # no-preference, reduce

        # Forced colors weights (most users don't use forced colors)
        self.forced_colors_weights = [0.95, 0.05]  # none, active

    def weighted_choice(self, choices: List, weights: List):
        """Chọn ngẫu nhiên với trọng số"""
        return random.choices(choices, weights=weights, k=1)[0]

    def weighted_choice_dict(self, choices_dict: Dict):
        """Chọn ngẫu nhiên từ dict với trọng số"""
        choices = list(choices_dict.keys())
        weights = list(choices_dict.values())
        return random.choices(choices, weights=weights, k=1)[0]

    def generate_device_name(
        self, device_type: Optional[str] = None, browser: Optional[str] = None
    ) -> str:
        """
        Tạo device name

        Args:
            device_type: 'desktop', 'mobile', 'tablet'
            browser: Tên browser cụ thể

        Returns:
            Device name string
        """
        # if device_type is None:
        #     device_type = random.choice(["desktop", "mobile", "tablet"])

        # if browser is None:
        #     browser = random.choice(self.devices[device_type]["browsers"])

        # # Format: "Device_Type Browser"
        # device_name = f"{device_type.title()} {browser}"
        
        device_name = "Desktop Chrome"

        return device_name

    def generate_locale_timezone(self, locale: Optional[str] = None) -> tuple:
        """
        Tạo locale và timezone tương ứng

        Args:
            locale: Locale cụ thể (optional)

        Returns:
            Tuple (locale, timezone_id)
        """
        if locale is None:
            locale = self.weighted_choice_dict(self.locales)

        # Lấy timezone phù hợp với locale
        if locale in self.timezone_mapping:
            timezone_id = random.choice(self.timezone_mapping[locale])
        else:
            # Fallback timezone
            timezone_id = random.choice(["UTC", "Europe/London", "America/New_York"])

        return locale, timezone_id

    def generate_display_preferences(self) -> Dict:
        """
        Tạo display preferences (color_scheme, reduced_motion, forced_colors)

        Returns:
            Dict với các preferences
        """
        color_scheme = self.weighted_choice(
            self.color_schemes, self.color_scheme_weights
        )
        reduced_motion = self.weighted_choice(
            self.reduced_motions, self.reduced_motion_weights
        )
        forced_colors = self.weighted_choice(
            self.forced_colors, self.forced_colors_weights
        )

        return {
            "color_scheme": color_scheme,
            "reduced_motion": reduced_motion,
            "forced_colors": forced_colors,
        }

    def generate_google_domain(self, locale: Optional[str] = None) -> str:
        """
        Tạo Google domain phù hợp với locale

        Args:
            locale: Locale để chọn domain phù hợp

        Returns:
            Google domain URL
        """
        if locale and locale in self.google_domains:
            # 70% chọn domain phù hợp với locale, 30% random
            if random.random() < 0.7:
                return random.choice(self.google_domains[locale])

        # Random domain
        all_domains = []
        for domains in self.google_domains.values():
            all_domains.extend(domains)
        all_domains.extend(self.additional_google_domains)

        return random.choice(list(set(all_domains)))  # Remove duplicates

    def generate_fingerprint(
        self,
        device_type: Optional[str] = None,
        browser: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> Dict:
        """
        Tạo một fingerprint hoàn chỉnh

        Args:
            device_type: 'desktop', 'mobile', 'tablet'
            browser: Browser name
            locale: Locale code

        Returns:
            Dict theo format yêu cầu
        """
        # Generate device name
        device_name = self.generate_device_name(device_type)

        # Generate locale và timezone
        locale, timezone_id = self.generate_locale_timezone(locale)

        # Generate display preferences
        display_prefs = self.generate_display_preferences()

        # Generate Google domain
        google_domain = self.generate_google_domain(locale)

        return {
            "fingerprint": {
                "device_name": device_name,
                "locale": locale,
                "timezone_id": timezone_id,
                "color_scheme": display_prefs["color_scheme"],
                "reduced_motion": display_prefs["reduced_motion"],
                "forced_colors": display_prefs["forced_colors"],
            },
            "google_domain": google_domain,
        }

    def generate_multiple_fingerprints(self, count: int = 5, **kwargs) -> List[Dict]:
        """
        Tạo nhiều fingerprints

        Args:
            count: Số lượng fingerprints
            **kwargs: Tham số cho generate_fingerprint()

        Returns:
            List các fingerprints
        """
        fingerprints = []

        for i in range(count):
            fingerprint = self.generate_fingerprint(**kwargs)
            fingerprint["id"] = i + 1
            fingerprint["generated_at"] = datetime.now().isoformat()
            fingerprints.append(fingerprint)

        return fingerprints

    def generate_fingerprint_pool(
        self, desktop_count: int = 10, mobile_count: int = 8, tablet_count: int = 5
    ) -> Dict:
        """
        Tạo pool fingerprints phân loại theo device type

        Args:
            desktop_count: Số fingerprints desktop
            mobile_count: Số fingerprints mobile
            tablet_count: Số fingerprints tablet

        Returns:
            Dict phân loại fingerprints
        """
        pool = {
            "desktop": self.generate_multiple_fingerprints(
                desktop_count, device_type="desktop"
            ),
            "mobile": self.generate_multiple_fingerprints(
                mobile_count, device_type="mobile"
            ),
            "tablet": self.generate_multiple_fingerprints(
                tablet_count, device_type="tablet"
            ),
            "metadata": {
                "total_count": desktop_count + mobile_count + tablet_count,
                "generated_at": datetime.now().isoformat(),
                "distribution": {
                    "desktop": desktop_count,
                    "mobile": mobile_count,
                    "tablet": tablet_count,
                },
            },
        }

        return pool

    def get_random_fingerprint(self) -> Dict:
        """Lấy một fingerprint ngẫu nhiên"""
        return self.generate_fingerprint()

    def save_fingerprint(self, fingerprint, filename: str):
        """Lưu fingerprints ra file JSON"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(fingerprint, f, indent=2, ensure_ascii=False)
        print(f"Đã lưu fingerprints vào {filename}")

    def load_fingerprints(self, filename: str):
        """Load fingerprints từ file JSON"""
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def print_fingerprint(self, fingerprint: Dict):
        """In fingerprint ra console một cách đẹp mắt"""
        print(json.dumps(fingerprint, indent=2, ensure_ascii=False))

    def fingerprint_with_proxy(self, fingerprint: Dict, proxy: Dict) -> Dict:
        """
        Kết hợp fingerprint với proxy

        Args:
            fingerprint: Fingerprint dict
            proxy: Proxy dict

        Returns:
            Dict kết hợp fingerprint và proxy
        """
        from proxy_helper import get_random_proxy
        
        proxy = get_random_proxy()
        locale = proxy["locale"]
        timezone_id = proxy["timezone_id"]

        # Generate fingerprint cố định locale + timezone
        fingerprint_data = self._fingerprint_generator.generate_fingerprint(locale=locale)
        fingerprint = fingerprint_data["fingerprint"]
        fingerprint["locale"] = locale
        fingerprint["timezone_id"] = timezone_id  # ép lại cho đúng theo proxy
       
        return fingerprint
    

# Ví dụ sử dụng
if __name__ == "__main__":
    # Khởi tạo generator
    generator = CustomFingerprintGenerator()

    print("=== Tạo một fingerprint ngẫu nhiên ===")
    single_fp = generator.generate_fingerprint()
    # generator.print_fingerprint(single_fp)

    # print("\n" + "=" * 50)
    # print("=== Tạo fingerprint cho desktop Chrome ===")
    # desktop_fp = generator.generate_fingerprint(device_type="desktop", browser="Chrome")
    # generator.print_fingerprint(desktop_fp)

    # print("\n" + "=" * 50)
    # print("=== Tạo 3 fingerprints mobile ===")
    # mobile_fps = generator.generate_multiple_fingerprints(count=3, device_type="mobile")

    # for fp in mobile_fps:
    #     generator.print_fingerprint(fp)
    #     print("-" * 30)

    # print("\n" + "=" * 50)
    # print("=== Tạo fingerprint pool ===")
    # pool = generator.generate_fingerprint_pool(
    #     desktop_count=3, mobile_count=2, tablet_count=1
    # )

    # print("Pool metadata:")
    # generator.print_fingerprint(pool["metadata"])

    # print("\nDesktop fingerprints:")
    # for fp in pool["desktop"]:
    #     print(
    #         f"- {fp['fingerprint']['device_name']} | {fp['fingerprint']['locale']} | {fp['google_domain']}"
    #     )

    # # Lưu fingerprints
    # generator.save_fingerprints(pool, "fingerprint_pool.json")

    # print("\n=== Random fingerprint rotation example ===")
    # for i in range(3):
    #     fp = generator.get_random_fingerprint()
    #     print(
    #         f"Rotation {i + 1}: {fp['fingerprint']['device_name']} | {fp['fingerprint']['locale']}"
    #     )

    # print("\n=== Lưu fingerprints vào file ===")
    # generator.save_fingerprint(single_fp, "single_fingerprint.json")
    from dataclasses import dataclass

    @dataclass
    class FingerprintConfig:
        """Cấu hình fingerprint cho browser"""
        device_name: str
        locale: str
        timezone_id: str
        color_scheme: str
        reduced_motion: str
        forced_colors: str

        def to_dict(self):
            return {
                'device_name': self.device_name,
                'locale': self.locale,
                'timezone_id': self.timezone_id,
                'color_scheme': self.color_scheme,
                'reduced_motion': self.reduced_motion,
                'forced_colors': self.forced_colors
            }
    fp = FingerprintConfig(
            device_name=single_fp['fingerprint']['device_name'],
            locale=single_fp['fingerprint']['locale'],
            timezone_id=single_fp['fingerprint']['timezone_id'],
            color_scheme=single_fp['fingerprint']['color_scheme'],
            reduced_motion=single_fp['fingerprint']['reduced_motion'],
            forced_colors=single_fp['fingerprint']['forced_colors']
        )
    print(fp.to_dict())
    
    