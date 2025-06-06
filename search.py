from playwright.async_api import async_playwright, Browser # Changed to async_api
from typing import Optional, List, Dict, Any
import os
import json
import logging
from datetime import datetime
import random
import re
from search_types import SearchResponse, FingerprintConfig, CommandOptions, SearchResult, SavedState, HtmlResponse
from config import DEVICE_CONFIGS, TIMEZONE_LIST, GOOGLE_DOMAINS
from bs4 import BeautifulSoup # Import BeautifulSoup

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSearcher:
    """
    Class chính để thực hiện Google Search
    
    Usage:
        s = GoogleSearcher()
        res = await s.search("python programming", limit=5, locale="vi-VN") # Usage with await
    """
    DEVICE_CONFIGS = DEVICE_CONFIGS
    GOOGLE_DOMAINS = GOOGLE_DOMAINS
    TIMEZONE_LIST = TIMEZONE_LIST
    
    def __init__(self, default_options: Optional[CommandOptions] = None):
        self.default_options = default_options or CommandOptions()
        self._browser: Optional[Browser] = None
        self._playwright = None
        self._playwright_context = None # To store the async context manager
    
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
                await context.storage_state(path=state_file) # await added
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
        
        context = await browser.new_context(**context_options) # await added
        
        await context.add_init_script(""" # await added
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
        
        await context.add_init_script(""" # await added
            Object.defineProperty(window.screen, 'width', { get: () => 1920 });
            Object.defineProperty(window.screen, 'height', { get: () => 1080 });
            Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
        """)
        
        return context
    
    async def find_search_input(self, page): # async added
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
                search_input = await page.query_selector(selector) # await added
                if search_input:
                    logger.info(f"Found search input with selector: {selector}")
                    return search_input
            except:
                continue
        
        return None
    
    async def perform_search_input(self, page, query: str, timeout: int): # async added
        """Thực hiện nhập search query"""
        search_input = await self.find_search_input(page) # await added
        if not search_input:
            raise Exception("Search input not found")
        
        await search_input.click() # await added
        await page.wait_for_timeout(self.get_random_delay(100, 300)) # await added
        await search_input.fill("") # await added
        await page.keyboard.type(query, delay=self.get_random_delay(10, 30)) # await added
        await page.wait_for_timeout(self.get_random_delay(100, 300)) # await added
        await page.keyboard.press("Enter") # await added
        await page.wait_for_load_state("networkidle", timeout=timeout) # await added
    
    async def wait_for_search_results(self, page, timeout: int): # async added
        """Chờ kết quả search xuất hiện"""
        selectors = [
            "#search",
            "#rso",
            ".g",
            "[data-sokoban-container]",
            "div[role='main']"
        ]
        
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=timeout // 2) # await added
                logger.info(f"Found search results with selector: {selector}")
                return True
            except:
                continue
        
        return False
    
    async def extract_search_results(self, page, limit: int) -> List[Dict[str, str]]: # async added
        """Trích xuất kết quả search từ trang"""
        await page.wait_for_timeout(self.get_random_delay(200, 500)) # await added
        results = await page.evaluate(""" # await added
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
    
    async def save_html_and_screenshot(self, page, html: str, query: str, output_path: Optional[str] = None) -> tuple: # async added
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
            await page.screenshot(path=screenshot_path, full_page=True) # await added
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")
            screenshot_path = None
        
        return output_path, screenshot_path
    
    async def init_browser(self, headless: bool = True, timeout: int = 60000, proxy: Optional[Dict[str, str]] = None): # async added
        """Khởi tạo browser"""
        if not self._playwright:
            self._playwright = async_playwright()  # Store the context manager
            self._playwright_context = await self._playwright.__aenter__()  # Store the Playwright object (await added)
        
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
            
            self._browser = await self._playwright_context.chromium.launch(**launch_options) # await added
            logger.info("Browser initialized successfully")
        
        return self._browser
    
    async def close_browser(self): # async added
        """Đóng browser"""
        if self._browser:
            try:
                await self._browser.close() # await added
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Failed to close browser: {e}")
            self._browser = None
        
        if self._playwright:
            try:
                await self._playwright.__aexit__(None, None, None)  # Call __aexit__ on the async context manager (await added)
                logger.info("Playwright context closed successfully")
            except Exception as e:
                logger.error(f"Failed to close Playwright context: {e}")
            self._playwright = None
            self._playwright_context = None
    
    async def perform_search(self, query: str, options: CommandOptions, headless: bool) -> SearchResponse: # async added
        """Thực hiện search và trả về kết quả"""
        saved_state = self.load_saved_state(options.state_file)
        browser = await self.init_browser(headless, options.timeout, options.proxy) # await added
        
        try:
            storage_state = options.state_file if os.path.exists(options.state_file) else None
            context = await self.setup_browser_context(browser, saved_state, storage_state, options.locale) # await added
            page = await context.new_page() # await added
            
            try:
                selected_domain = saved_state.google_domain or random.choice(self.GOOGLE_DOMAINS)
                saved_state.google_domain = selected_domain
                
                logger.info(f"Navigating to {selected_domain}")
                await page.goto(selected_domain, timeout=options.timeout, wait_until="networkidle") # await added
                
                if self.check_captcha_or_sorry(page):
                    if headless:
                        logger.warning("Detected CAPTCHA, retrying in headed mode")
                        await page.close() # await added
                        await context.close() # await added
                        return await self.perform_search(query, options, False) # await added
                    else:
                        logger.warning("CAPTCHA detected, please complete verification")
                        await page.wait_for_url( # await added
                            lambda url: not any(p in url.lower() for p in ["sorry", "recaptcha", "captcha"]),
                            timeout=options.timeout * 2
                        )
                
                logger.info(f"Searching for: {query}")
                await self.perform_search_input(page, query, options.timeout) # await added
                
                if self.check_captcha_or_sorry(page):
                    if headless:
                        logger.warning("Detected CAPTCHA after search, retrying in headed mode")
                        await page.close() # await added
                        await context.close() # await added
                        return await self.perform_search(query, options, False) # await added
                    else:
                        logger.warning("CAPTCHA detected after search, please complete verification")
                        await page.wait_for_url( # await added
                            lambda url: not any(p in url.lower() for p in ["sorry", "recaptcha", "captcha"]),
                            timeout=options.timeout * 2
                        )
                
                if not await self.wait_for_search_results(page, options.timeout): # await added
                    raise Exception("Search results not found")
                
                results_data = await self.extract_search_results(page, options.limit) # await added
                results = results_data
                
                if not options.no_save_state:
                    await self.save_browser_state(context, options.state_file, saved_state) # await added
                
                await page.close() # await added
                await context.close() # await added
                
                logger.info(f"Found {len(results)} results")
                return results # Returning raw list of dicts for simplicity or convert to SearchResult objects if needed
            
            except Exception as e:
                logger.error(f"Search error: {e}")
                await page.close() # await added
                await context.close() # await added
                return [
                    SearchResult(title="Search Failed", link="", snippet=f"Error: {str(e)}")
                ]
        
        except Exception as e:
            logger.error(f"Browser setup error: {e}")
            return [
                SearchResult(title="Search Failed", link="", snippet=f"Browser setup error: {str(e)}")
            ]
    
    async def perform_get_html(self, query: str, options: CommandOptions, headless: bool) -> HtmlResponse: # async added
        """Lấy HTML của trang search"""
        saved_state = self.load_saved_state(options.state_file)
        browser = await self.init_browser(headless, options.timeout, options.proxy) # await added
        
        try:
            storage_state = options.state_file if os.path.exists(options.state_file) else None
            context = await self.setup_browser_context(browser, saved_state, storage_state, options.locale) # await added
            page = await context.new_page() # await added
            
            try:
                selected_domain = saved_state.google_domain or random.choice(self.GOOGLE_DOMAINS)
                saved_state.google_domain = selected_domain
                
                logger.info(f"Navigating to {selected_domain}")
                await page.goto(selected_domain, timeout=options.timeout, wait_until="networkidle") # await added
                
                if self.check_captcha_or_sorry(page):
                    if headless:
                        logger.warning("Detected CAPTCHA, retrying in headed mode")
                        await page.close() # await added
                        await context.close() # await added
                        return await self.perform_get_html(query, options, False) # await added
                    else:
                        logger.warning("CAPTCHA detected, please complete verification")
                        await page.wait_for_url( # await added
                            lambda url: not any(p in url.lower() for p in ["sorry", "recaptcha", "captcha"]),
                            timeout=options.timeout * 2
                        )
                
                logger.info(f"Searching for: {query}")
                await self.perform_search_input(page, query, options.timeout) # await added
                
                if self.check_captcha_or_sorry(page):
                    if headless:
                        logger.warning("Detected CAPTCHA after search, retrying in headed mode")
                        await page.close() # await added
                        await context.close() # await added
                        return await self.perform_get_html(query, options, False) # await added
                    else:
                        logger.warning("CAPTCHA detected after search, please complete verification")
                        await page.wait_for_url( # await added
                            lambda url: not any(p in url.lower() for p in ["sorry", "recaptcha", "captcha"]),
                            timeout=options.timeout * 2
                        )
                
                await page.wait_for_timeout(1000)  # Ensure page stability # await added
                await page.wait_for_load_state("networkidle", timeout=options.timeout) # await added
                
                final_url = page.url
                full_html = await page.content() # await added
                html = self.clean_html_content(full_html)
                
                saved_file_path = None
                screenshot_path = None
                if options.save_html:
                    saved_file_path, screenshot_path = await self.save_html_and_screenshot( # await added
                        page, full_html, query, options.output_path
                    )
                
                if not options.no_save_state:
                    await self.save_browser_state(context, options.state_file, saved_state) # await added
                
                await page.close() # await added
                await context.close() # await added

                # return full_html
                
                return HtmlResponse(
                    query=query,
                    html=html,
                    url=final_url,
                    saved_path=saved_file_path,
                    screenshot_path=screenshot_path,
                    original_html_length=len(full_html)
                )
            
            except Exception as e:
                logger.error(f"HTML retrieval error: {e}")
                await page.close() # await added
                await context.close() # await added
                raise Exception(f"Failed to get HTML: {str(e)}")
        
        except Exception as e:
            logger.error(f"Browser setup error: {e}")
            raise Exception(f"Failed to setup browser: {str(e)}")
    
    async def search(self, query: str, limit: int = 10, locale: str = "vi_VN") -> SearchResponse: # async added
        """Public method để search"""
        options = CommandOptions(limit=limit, locale=locale)
        try:
            return await self.perform_search(query, options, True) # await added
        finally:
            await self.close_browser() # await added
    
    async def get_html(self, query: str, save_to_file: bool = False, locale: str = "vi-VN", 
                 output_path: Optional[str] = None) -> HtmlResponse: # async added
        """Public method để lấy HTML"""
        rand = random.randint(1,10)
        if rand==1:
            os.remove("browser_state.json")

        options = CommandOptions(save_html=save_to_file, locale=locale, output_path=output_path)
        try:
            return await self.perform_get_html(query, options, True) # await added
        finally:
            await self.close_browser() # await added

import asyncio # Import asyncio to run async functions

if __name__ == "__main__":
    async def main(): # Define an async main function
        s = GoogleSearcher()
        import pprint

        # Get HTML content
        html_response = await s.get_html("VN Index hôm nay",save_to_file=True)
        # print(type(html_response))

        # pprint.pp(html_response)

        if html_response.html:
            soup = BeautifulSoup(html_response.html, "html.parser")
            print("Successfully parsed HTML with BeautifulSoup. Title:")
            print(soup.title.string if soup.title else "No title found")
            print(type(html_response.html))
            # You can now perform further parsing with Beautiful Soup
            # For example, find all links:
            # for a_tag in soup.find_all('a'):
            #     print(a_tag.get('href'))
        else:
            print("Failed to retrieve HTML.")
        
        # Example of search
        # search_results = await s.search("vnindex hôm nay", limit=5, locale="vi_VN")
        # pprint.pprint(search_results)

        await s.close_browser() # Ensure browser is closed even if not explicitly in `finally` blocks of `search` or `get_html`

    asyncio.run(main()) # Run the async main function