from playwright.async_api import async_playwright, Browser
from typing import Optional, List, Dict, Any
import os
import json
import logging
from datetime import datetime
import random
import re
from search_types import SearchResponse, FingerprintConfig, CommandOptions, SearchResult, SavedState, HtmlResponse
from config import DEVICE_CONFIGS, TIMEZONE_LIST, GOOGLE_DOMAINS

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSearcher:
    """
    Class chính để thực hiện Google Search (Async version)
    
    Usage:
        s = GoogleSearcher()
        res = await s.search("python programming", limit=5, locale="vi-VN")
    """
    DEVICE_CONFIGS = DEVICE_CONFIGS
    GOOGLE_DOMAINS = GOOGLE_DOMAINS
    TIMEZONE_LIST = TIMEZONE_LIST
    
    def __init__(self, default_options: Optional[CommandOptions] = None):
        self.default_options = default_options or CommandOptions()
        self._browser: Optional[Browser] = None
        self._playwright = None
    
    def get_host_machine_config(self, user_locale: Optional[str] = None) -> FingerprintConfig:
        """Tạo cấu hình fingerprint dựa trên máy host"""
        system_locale = user_locale or os.getenv("LANG", "vi-VN")
        
        # Approximate timezone based on offset
        offset = datetime.now().utcoffset()
        if offset:
            offset_minutes = offset.total_seconds() / 60
        else:
            offset_minutes = 0
        
        timezone_id = "Asia/Ho_Chi_Minh"
        if offset_minutes == -480:
            timezone_id = "Asia/Shanghai"
        elif offset_minutes == -540:
            timezone_id = "Asia/Tokyo"
        elif offset_minutes == -420:
            timezone_id = "Asia/Bangkok"
        elif offset_minutes == 0:
            timezone_id = "Europe/London"
        elif offset_minutes == 60:
            timezone_id = "Europe/Berlin"
        elif offset_minutes == 300:
            timezone_id = "America/New_York"
        
        hour = datetime.now().hour
        color_scheme = "dark" if hour >= 19 or hour < 7 else "light"
        reduced_motion = "no-preference"
        forced_colors = "none"
        
        platform = os.name
        device_name = "Desktop Chrome"
        if platform == "posix" and "darwin" in os.uname().sysname.lower():
            device_name = "Desktop Safari"
        elif platform == "nt":
            device_name = "Desktop Edge"
        elif platform == "posix":
            device_name = "Desktop Firefox"
        
        return FingerprintConfig(
            device_name=device_name,
            locale=system_locale,
            timezone_id=timezone_id,
            color_scheme=color_scheme,
            reduced_motion=reduced_motion,
            forced_colors=forced_colors
        )
    
    def get_random_delay(self, min_ms: int, max_ms: int) -> int:
        """Tạo delay ngẫu nhiên"""
        return random.randint(min_ms, max_ms)
    
    def load_saved_state(self, state_file: str) -> SavedState:
        """Load trạng thái đã lưu"""
        saved_state = SavedState()
        fingerprint_file = state_file.replace(".json", "-fingerprint.json")
        
        if os.path.exists(state_file):
            logger.info(f"Found browser state file: {state_file}")
            if os.path.exists(fingerprint_file):
                try:
                    with open(fingerprint_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        saved_state.fingerprint = FingerprintConfig(**data.get("fingerprint", {}))
                        saved_state.google_domain = data.get("google_domain")
                except Exception as e:
                    logger.warning(f"Failed to load fingerprint file: {e}")
        
        return saved_state
    
    async def save_browser_state(self, context, state_file: str, saved_state: SavedState, no_save_state: bool = False):
        """Lưu trạng thái browser"""
        if not no_save_state:
            try:
                fingerprint_file = state_file.replace(".json", "-fingerprint.json")
                os.makedirs(os.path.dirname(fingerprint_file), exist_ok=True)
                await context.storage_state(path=state_file)
                with open(fingerprint_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "fingerprint": saved_state.fingerprint.to_dict(),
                        "google_domain": saved_state.google_domain
                    }, f, indent=2)
                logger.info(f"Browser state saved to {state_file}")
            except Exception as e:
                logger.error(f"Failed to save state: {e}")
    
    async def setup_browser_context(self, browser: Browser, saved_state: SavedState, 
                             storage_state: Optional[str], locale: Optional[str]):
        """Thiết lập browser context với fingerprinting"""
        device_name = saved_state.fingerprint.device_name if saved_state.fingerprint else "Desktop Chrome"
        device_config = self.DEVICE_CONFIGS.get(device_name, self.DEVICE_CONFIGS["Desktop Chrome"])
        context_options = device_config.copy()
        
        if saved_state.fingerprint:
            context_options.update({
                "locale": saved_state.fingerprint.locale,
                "timezone_id": saved_state.fingerprint.timezone_id,
                "color_scheme": saved_state.fingerprint.color_scheme,
                "reduced_motion": saved_state.fingerprint.reduced_motion,
                "forced_colors": saved_state.fingerprint.forced_colors
            })
        else:
            host_config = self.get_host_machine_config(locale)
            context_options.update({
                "locale": host_config.locale,
                "timezone_id": host_config.timezone_id,
                "color_scheme": host_config.color_scheme,
                "reduced_motion": host_config.reduced_motion,
                "forced_colors": host_config.forced_colors
            })
            saved_state.fingerprint = host_config
        
        context_options.update({
            "permissions": ["geolocation", "notifications"],
            "accept_downloads": True,
            "is_mobile": False,
            "has_touch": False,
            "java_script_enabled": True
        })
        
        if storage_state:
            context_options["storage_state"] = storage_state
        
        context = await browser.new_context(**context_options)
        
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['vi-VN', 'en-US', 'en'] });
            window.chrome = { runtime: {}, loadTimes: () => {}, csi: () => {}, app: {} };
            if (typeof WebGLRenderingContext !== 'undefined') {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'Intel Inc.';
                    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                    return getParameter.call(this, parameter);
                };
            }
        """)
        
        await context.add_init_script("""
            Object.defineProperty(window.screen, 'width', { get: () => 1920 });
            Object.defineProperty(window.screen, 'height', { get: () => 1080 });
            Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
        """)
        
        return context
    
    async def find_search_input(self, page):
        """Tìm input search trên trang Google"""
        selectors = [
            "textarea[name='q']",
            "input[name='q']",
            "textarea[title='Search']",
            "input[title='Search']",
            "textarea[aria-label='Search']",
            "input[aria-label='Search']",
            "textarea"
        ]
        
        for selector in selectors:
            try:
                search_input = await page.query_selector(selector)
                if search_input:
                    logger.info(f"Found search input with selector: {selector}")
                    return search_input
            except:
                continue
        
        return None
    
    async def perform_search_input(self, page, query: str, timeout: int):
        """Thực hiện nhập search query"""
        search_input = await self.find_search_input(page)
        if not search_input:
            raise Exception("Search input not found")
        
        await search_input.click()
        await page.wait_for_timeout(self.get_random_delay(100, 300))
        await search_input.fill("")
        await page.keyboard.type(query, delay=self.get_random_delay(10, 30))
        await page.wait_for_timeout(self.get_random_delay(100, 300))
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle", timeout=timeout)
    
    async def wait_for_search_results(self, page, timeout: int):
        """Chờ kết quả search xuất hiện"""
        selectors = [
            "#search",
            "#rso",
            ".g",
            "[data-sokoban-container]",
            "div[role='main']",
            "div[data-header-feature] div",          
            "div[data-sokoban-container] .tF2Cxc" 
        ]
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=timeout // 2)
                logger.info(f"Found search results with selector: {selector}")
                return True
            except:
                continue
        
        return False
    
    async def extract_search_results(self, page, limit: int) -> List[Dict[str, str]]:
        """Trích xuất kết quả search từ trang"""
        await page.wait_for_timeout(self.get_random_delay(200, 500))
        results = await page.evaluate("""
            (maxResults) => {
                const results = [];
                const seenUrls = new Set();
                
                const selectorSets = [
                    { container: '#search div[data-hveid]', title: 'h3', snippet: '.VwiC3b' },
                    { container: '#rso div[data-hveid]', title: 'h3', snippet: '[data-sncf="1"]' },
                    { container: '.g', title: 'h3', snippet: 'div[style*="webkit-line-clamp"]' },
                    { container: 'div[jscontroller][data-hveid]', title: 'h3', snippet: 'div[role="text"]' }
                ];
                
                const altSnippetSelectors = ['.VwiC3b', '[data-sncf="1"]', 'div[style*="webkit-line-clamp"]', 'div[role="text"]'];
                
                for (const selectors of selectorSets) {
                    if (results.length >= maxResults) break;
                    const containers = document.querySelectorAll(selectors.container);
                    
                    for (const container of containers) {
                        if (results.length >= maxResults) break;
                        const titleElement = container.querySelector(selectors.title);
                        if (!titleElement) continue;
                        
                        const title = (titleElement.textContent || "").trim();
                        let link = '';
                        
                        const linkInTitle = titleElement.querySelector('a');
                        if (linkInTitle) {
                            link = linkInTitle.href;
                        } else {
                            let current = titleElement;
                            while (current && current.tagName !== 'A') {
                                current = current.parentElement;
                            }
                            if (current) {
                                link = current.href;
                            } else {
                                const containerLink = container.querySelector('a');
                                if (containerLink) {
                                    link = containerLink.href;
                                }
                            }
                        }
                        
                        if (!link || !link.startsWith('http') || seenUrls.has(link)) continue;
                        
                        let snippet = '';
                        let snippetElement = container.querySelector(selectors.snippet);
                        if (snippetElement) {
                            snippet = (snippetElement.textContent || "").trim();
                        } else {
                            for (const altSelector of altSnippetSelectors) {
                                snippetElement = container.querySelector(altSelector);
                                if (snippetElement) {
                                    snippet = (snippetElement.textContent || "").trim();
                                    break;
                                }
                            }
                            if (!snippet) {
                                const textNodes = Array.from(container.querySelectorAll('div')).filter(el =>
                                    !el.querySelector('h3') && (el.textContent || "").trim().length > 20
                                );
                                if (textNodes.length > 0) {
                                    snippet = (textNodes[0].textContent || "").trim();
                                }
                            }
                        }
                        
                        if (title && link) {
                            results.push({ title, link, snippet });
                            seenUrls.add(link);
                        }
                    }
                }
                
                if (results.length < maxResults) {
                    const anchorElements = Array.from(document.querySelectorAll("a[href^='http']"));
                    for (const el of anchorElements) {
                        if (results.length >= maxResults) break;
                        const link = el.href;
                        if (!link || seenUrls.has(link) || link.includes("google.com/") || 
                            link.includes("accounts.google") || link.includes("support.google")) continue;
                        
                        const title = (el.textContent || "").trim();
                        if (!title) continue;
                        
                        let snippet = '';
                        let parent = el.parentElement;
                        for (let i = 0; i < 3 && parent; i++) {
                            const text = (parent.textContent || "").trim();
                            if (text.length > 20 && text !== title) {
                                snippet = text;
                                break;
                            }
                            parent = parent.parentElement;
                        }
                        
                        results.push({ title, link, snippet });
                        seenUrls.add(link);
                    }
                }
                
                return results.slice(0, maxResults);
            }
        """, limit)
        
        return results
    
    def check_captcha_or_sorry(self, page) -> bool:
        """Kiểm tra CAPTCHA hoặc sorry page"""
        sorry_patterns = [
            "google.com/sorry",
            "recaptcha",
            "captcha",
            "unusual traffic"
        ]
        return any(pattern in page.url.lower() for pattern in sorry_patterns)
    
    def clean_html_content(self, html: str) -> str:
        """Làm sạch HTML content"""
        html = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)
        return html
    
    async def save_html_and_screenshot(self, page, html: str, query: str, output_path: Optional[str] = None) -> tuple:
        """Lưu HTML và screenshot"""
        if not output_path:
            output_dir = "./google-search-html"
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            sanitized_query = re.sub(r'[^a-zA-Z0-9]', '_', query)[:50]
            output_path = f"{output_dir}/{sanitized_query}-{timestamp}.html"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        screenshot_path = output_path.replace(".html", ".png")
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")
            screenshot_path = None
        
        return output_path, screenshot_path
    
    async def init_browser(self, headless: bool = True, timeout: int = 60000, proxy: Optional[Dict[str, str]] = None):
        """Khởi tạo browser"""
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        if not self._browser:
            args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--disable-web-security",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--hide-scrollbars",
                "--mute-audio",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-component-extensions-with-background-pages",
                "--disable-extensions",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-renderer-backgrounding",
                "--enable-features=NetworkService,NetworkServiceInProcess",
                "--force-color-profile=srgb",
                "--metrics-recording-only"
            ]
            if os.name != "nt":  # Avoid --no-sandbox on Windows unless necessary
                args.extend(["--no-sandbox", "--disable-setuid-sandbox"])
            
            launch_options = {
                "headless": headless,
                "timeout": timeout * 2,
                "args": args,
                "ignore_default_args": ["--enable-automation"]
            }
            if proxy:
                launch_options["proxy"] = proxy
            
            self._browser = await self._playwright.chromium.launch(**launch_options)
            logger.info("Browser initialized successfully")
        
        return self._browser
    
    async def close_browser(self):
        """Đóng browser"""
        if self._browser:
            try:
                await self._browser.close()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Failed to close browser: {e}")
            self._browser = None
        
        if self._playwright:
            try:
                await self._playwright.stop()
                logger.info("Playwright context closed successfully")
            except Exception as e:
                logger.error(f"Failed to close Playwright context: {e}")
            self._playwright = None
    
    async def perform_search(self, query: str, options: CommandOptions, headless: bool) -> str:
        """Thực hiện search và trả về kết quả"""
        saved_state = self.load_saved_state(options.state_file)
        browser = await self.init_browser(headless, options.timeout, options.proxy)
        
        try:
            storage_state = options.state_file if os.path.exists(options.state_file) else None
            context = await self.setup_browser_context(browser, saved_state, storage_state, options.locale)
            page = await context.new_page()
            
            try:
                selected_domain = saved_state.google_domain or random.choice(self.GOOGLE_DOMAINS)
                saved_state.google_domain = selected_domain
                
                logger.info(f"Navigating to {selected_domain}")
                await page.goto(selected_domain, timeout=options.timeout, wait_until="networkidle")
                logger.info(f"Current page URL after navigation: {page.url}")

                if self.check_captcha_or_sorry(page):
                    if headless:
                        logger.warning("Detected CAPTCHA, retrying in headed mode")
                        await page.close()
                        await context.close()
                        return await self.perform_search(query, options, False)
                    else:
                        logger.warning("CAPTCHA detected, please complete verification")
                        await page.wait_for_url(
                            lambda url: not any(p in url.lower() for p in ["sorry", "recaptcha", "captcha"]),
                            timeout=options.timeout * 2
                        )
                
                logger.info(f"Searching for: {query}")
                await self.perform_search_input(page, query, options.timeout)
                
                if self.check_captcha_or_sorry(page):
                    if headless:
                        logger.warning("Detected CAPTCHA after search, retrying in headed mode")
                        await page.close()
                        await context.close()
                        return await self.perform_search(query, options, False)
                    else:
                        logger.warning("CAPTCHA detected after search, please complete verification")
                        await page.wait_for_url(
                            lambda url: not any(p in url.lower() for p in ["sorry", "recaptcha", "captcha"]),
                            timeout=options.timeout * 2
                        )
                
                if not await self.wait_for_search_results(page, options.timeout):
                    html_debug = await page.content()
                    with open("debug_google_page.html", "w", encoding="utf-8") as f:
                        f.write(html_debug)
                    raise Exception("Search results not found")
                
                full_html = await page.content()
              
                results_data = await self.extract_search_results(page, options.limit)
                results = results_data
                
                if not options.no_save_state:
                    await self.save_browser_state(context, options.state_file, saved_state)
                await self.save_html_and_screenshot(page, full_html, query)

                await page.close()
                await context.close()
                
                logger.info(f"Found {len(results)} results")
                return full_html
                # return SearchResponse(query=query, results=results)
            
            except Exception as e:
                logger.error(f"Search error: {e}")
                await page.close()
                await context.close()
                return SearchResponse(query=query, results=[
                    SearchResult(title="Search Failed", link="", snippet=f"Error: {str(e)}")
                ])
        
        except Exception as e:
            logger.error(f"Browser setup error: {e}")
            return SearchResponse(query=query, results=[
                SearchResult(title="Search Failed", link="", snippet=f"Browser setup error: {str(e)}")
            ])
    
    async def search(self, query: str, limit: int = 10, locale: str = "vi_VN") -> SearchResponse:
        """Public method để search"""
        options = CommandOptions(limit=limit, locale=locale)
        try:
            
            return await self.perform_search(query, options, True)
        except Exception as e:
            print('Lỗi', e)
            return None
        finally:
            await self.close_browser()

if __name__ == "__main__":
    import asyncio
    
    async def main():
        s = GoogleSearcher()
        import pprint
        result = await s.get_html("VN Index hôm nay",save_to_file=True)
        # with open("search.html", "w", encoding="utf-8") as f:
        #     f.write(result)
        # pprint.pp(result)
        print(type(result))
        await s.close_browser()
    
    asyncio.run(main())