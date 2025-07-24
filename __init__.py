"""googlesearch is a Python library for searching Google, easily."""
# from time import sleep
# from bs4 import BeautifulSoup
from requests import get
from urllib.parse import unquote # to decode the url
from user_agents import get_useragent
from requests_html import AsyncHTMLSession
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def _async_req(term, results, lang, start, proxies, timeout, safe, ssl_verify, region, endpoint, cookies= {
            'CONSENT': 'PENDING+987', # Bypasses the consent page
            'SOCS': 'CAESHAgBEhIaAB',
        }):
    
    asession = AsyncHTMLSession()

    url = "https://www.ecosia.org/search"  

    escaped_term = term.replace(" ", "+")
        
    logger.info(f"params: {escaped_term}")

    r = await asession.get(
        url=url,
        headers={
            "User-Agent": get_useragent(),
            "Accept": "*/*"
        },
        params={
            "method": "index",            
            "q": escaped_term,
        },
        proxies=proxies,
        timeout=timeout,
        verify=ssl_verify,
        cookies = cookies
    )
    await r.html.arender(sleep=2)  # render JS với delay 2 giây

    # # Regex để lấy đoạn giữa hai điểm
    # pattern = r'<div class="gsc-resultsbox-visible">(.*)'
    # match = re.search(pattern, r.html.html, re.DOTALL)

    # if match:
    #     content = match.group(1)
    #     logger.info(f"[REQUESTS] Đã tìm thấy {len(match.group(0))} khối JSON trong HTML.")

    with open("google.html", "w", encoding="utf-8") as f:
        
        f.write(r.html.html)

    r.raise_for_status()

    return r

async def asearch(term, num_results=3, lang="vi", proxy=None, advanced=True, sleep_interval=0, timeout=5, safe="active", ssl_verify=None, region=None, start_num=0, unique=True, endpoint="luxirty"):
    """Search the Google search engine"""

    # Proxy setup
    # proxies = {"https": proxy, "http": proxy} if proxy and (proxy.startswith("https") or proxy.startswith("http") or proxy.startswith("socks5")) else None
    proxies = {
        "https": proxy,
        "http": proxy
        } if proxy else None
    
    start = start_num
    fetched_results = 0  # Keep track of the total fetched results
    # fetched_links = set() # to keep track of links that are already seen previously
    try:
        # logger.info(f"endpoint: {endpoint}")
        resp = await _async_req(term, num_results - start, lang, start, proxies, timeout, safe, ssl_verify, region, endpoint=endpoint)
        with open("google.html", "w", encoding="utf-8") as f:
            f.write(resp)
        return resp
    except Exception as e:
        logger.error(f"Lỗi khi gửi request: {e}")
        return None  


def _req(term, results, lang, start, proxies, timeout, safe, ssl_verify, region, endpoint, cookies= {
            'CONSENT': 'PENDING+987', # Bypasses the consent page
            'SOCS': 'CAESHAgBEhIaAB',
        }):
    
    params = {
    "q": term
    }
    # logger.info(f"endpoint: {endpoint}")
    if endpoint == "aol":
        url = "https://search.aol.com/aol/search"
    elif endpoint == "mullvad leta":
        url = "https://leta.mullvad.net/search"
        params["engine"] = "google"
    elif endpoint == "brave":
        url = "https://search.brave.com/search"  
    elif endpoint == "duckduckgo":
        url = "https://duckduckgo.com/"
    elif endpoint == "yahoo":
        url = "https://search.yahoo.com/search"
    elif endpoint == "bing":
        url = "https://www.bing.com/search"
        params["pq"] = "vn"

        # escaped_term = term.replace(" ", "+")

    resp = get(
        url=url,
        headers={
            "User-Agent": get_useragent(),
            "Accept": "*/*"
        },
        params=params,
        proxies=proxies,
        timeout=timeout,
        verify=ssl_verify,
        cookies = cookies
    )
    resp.raise_for_status()
    return resp


class SearchResult:
    def __init__(self, url, title, description):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"


def search(term, num_results=3, lang="vi", proxy=None, advanced=True, sleep_interval=0, timeout=30, safe="active", ssl_verify=None, region=None, start_num=0, unique=True, endpoint="luxirty"):
    """Search the Google search engine"""

    # Proxy setup
    # proxies = {"https": proxy, "http": proxy} if proxy and (proxy.startswith("https") or proxy.startswith("http") or proxy.startswith("socks5")) else None
    proxies = {
        "https": proxy,
        "http": proxy
        } if proxy else None
    
    start = start_num
    fetched_results = 0  # Keep track of the total fetched results
    # fetched_links = set() # to keep track of links that are already seen previously
    try:
        # logger.info(f"endpoint: {endpoint}")
        resp = _req(term, num_results - start, lang, start, proxies, timeout, safe, ssl_verify, region, endpoint=endpoint)
        if resp is None:
            logger.error(f"❌ Không nhận được phản hồi từ hàm `_req` (resp is None). Endpoint: {endpoint}, Query: {term}")
            return None
    except Exception as e:
        # print(f"Lỗi khi gửi request: {e}")
        logger.error(f"Lỗi khi gửi request: {e}")
        return None

    if resp.status_code == 200:
        g_cookies = resp.cookies.get_dict()

    while fetched_results < num_results:
        try:
            resp = _req(term, num_results - start, lang, start, proxies, timeout, safe, ssl_verify, region, cookies = g_cookies, endpoint=endpoint)
            if resp.status_code == 200:
                g_cookies = resp.cookies.get_dict()
            else:
                logger.error(f"URL: {resp.url}")
                logger.error(f"Request failed with status code: {resp.status_code}")
                logger.error(f"Response content: {resp.content}")
                # logger.error(f"Response text: {resp.text[:200]}")
                # logger.error(f"Response headers: {resp.headers}")
            # with open("google.html", "w", encoding="utf-8") as f:
            #     f.write(resp.text)
            # logger.info(f"Response text: {resp.text}...")  # Log first 200 characters
            return resp
        except Exception as e:
            # print(f"Lỗi khi gửi request: {e}")
            return None
        
if __name__ == "__main__":
    for i in range(2):
        print("--------------------------------------------------", i)
        search("giá vàng hôm nay")
        