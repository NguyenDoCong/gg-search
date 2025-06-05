from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class SearchResult:
    """Kết quả search đơn lẻ"""
    title: str
    link: str
    snippet: str

@dataclass
class SearchResponse:
    """Lớp chứa dữ liệu kết quả search"""
    query: str
    results: List[SearchResult]

@dataclass
class HtmlResponse:
    """Lớp chứa HTML content"""
    query: str
    html: str
    url: str
    saved_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    original_html_length: int = 0

@dataclass
class CommandOptions:
    """Tùy chọn cho search"""
    state_file: str = "./browser_state.json"
    no_save_state: bool = False
    timeout: int = 60000
    limit: int = 10
    locale: Optional[str] = None
    headless: bool = True
    save_html: bool = False
    output_path: Optional[str] = None
    proxy: Optional[Dict[str, str]] = None

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

@dataclass
class SavedState:
    """Lớp chứa trạng thái đã lưu của browser"""
    fingerprint: Optional[FingerprintConfig] = None
    google_domain: Optional[str] = None