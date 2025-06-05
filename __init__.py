"""googlesearch is a Python library for searching Google, easily."""
# from time import sleep
# from bs4 import BeautifulSoup
from requests import get
from urllib.parse import unquote # to decode the url
from user_agents import get_useragent
import pprint

def _req(term, results, lang, start, proxies, timeout, safe, ssl_verify, region, cookies= {
            'CONSENT': 'PENDING+987', # Bypasses the consent page
            'SOCS': 'CAESHAgBEhIaAB',
        }):
    resp = get(
        url="https://www.google.com/search",
        headers={
            "User-Agent": get_useragent(),
            "Accept": "*/*"
        },
        params={
            "q": term,
            "num": results + 2,  # Prevents multiple requests
            "hl": lang,
            "start": start,
            "safe": safe,
            "gl": region,
        },
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


def search(term, num_results=3, lang="vi", proxy=None, advanced=True, sleep_interval=0, timeout=5, safe="active", ssl_verify=None, region=None, start_num=0, unique=True):
    """Search the Google search engine"""

    # Proxy setup
    proxies = {"https": proxy, "http": proxy} if proxy and (proxy.startswith("https") or proxy.startswith("http") or proxy.startswith("socks5")) else None
    # proxies = {
    # 'http': 'socks5h://127.0.0.1:9050',
    # 'https': 'socks5h://127.0.0.1:9050'
    # }
    start = start_num
    fetched_results = 0  # Keep track of the total fetched results
    # fetched_links = set() # to keep track of links that are already seen previously
    try:
        resp = _req(term, num_results - start, lang, start, proxies, timeout, safe, ssl_verify, region)
    except Exception as e:
        print(f"Lỗi khi gửi request: {e}")
        return None

    if resp.status_code == 200:
        g_cookies = resp.cookies.get_dict()

    while fetched_results < num_results:
        try:
            resp = _req(term, num_results - start, lang, start, proxies, timeout, safe, ssl_verify, region, cookies = g_cookies)
            if resp.status_code == 200:
                g_cookies = resp.cookies.get_dict()
            with open("google.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            pprint.pp(resp.text)
            return resp
        except Exception as e:
            print(f"Lỗi khi gửi request: {e}")
            return None
        
if __name__ == "__main__":
    for i in range(1000):
        print("--------------------------------------------------", i)
        search("giá vàng hôm nay")
        