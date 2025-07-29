from contextlib import asynccontextmanager
import random
from bs4 import BeautifulSoup
from __init__ import search, asearch
from search import GoogleSearcher
from fastapi import FastAPI, Request
# from contextlib import asynccontextmanager
import uvicorn
from fastapi.responses import JSONResponse
# from playwright.async_api import async_playwright, Browser, BrowserContext
import asyncio
from aiocache import cached
from async_batcher.batcher import Batcher
from dataclasses import dataclass
from typing import List, Tuple
from async_batcher.utils.data_handling import process_result
# search_count = 0
# search_lock = asyncio.Lock()
from proxy.proxy_pool import ProxyPool
import re
import json
import logging
import chardet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # app.state.luxirty_instance = GoogleSearcher(use_proxy_fingerprint=True)
    # app.state.search_instance = GoogleSearcher(use_proxy_fingerprint=True)
    
    # ✅ Gọi init_browser() sau khi khởi tạo
    # await app.state.search_instance.init_browser()
    # # await app.state.google_instance.init_browser()   
    # await app.state.search_instance._create_context()
    # # await app.state.google_instance._create_contexts(domain="google")

    proxy_ports = [9050 + i * 2 for i in range(80)]  # Dùng chính xác 160 instance
    proxy_pool = ProxyPool()

    # if not proxy_pool.redis.exists("tor:proxy_list"):
    #     proxy_pool.init_proxies(proxy_ports)
    #     logger.info(f"[INIT] ✅ Đã khởi tạo {len(proxy_ports)} proxy Tor vào Redis.")
    # else:
    #     logger.info("[INIT] ♻️ Proxy list đã tồn tại trong Redis.")

    existing_count = proxy_pool.redis.llen("tor:proxy_list")

    if existing_count != len(proxy_ports):
        proxy_pool.redis.delete("tor:proxy_list")
        proxy_pool.init_proxies(proxy_ports)
        logger.info(f"[INIT] 🔁 Proxy list reset: {len(proxy_ports)} proxies loaded.")
    else:
        logger.info(f"[INIT] ♻️ Proxy list đã tồn tại với {existing_count} proxies.")
    
    loop = asyncio.get_running_loop()
    task = asyncio.create_task(batcher.start(loop))
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

app = FastAPI(lifespan=lifespan)

# @cached(ttl=86400)  # Cache kết quả trong 1 giờ (3600 giây)
async def search_response(query, request: Request, method="fingerprint", endpoint="luxirty", retries=0):
    # global luxirty_instance, google_instance, search_count
    proxy_pool = ProxyPool()
    proxy = proxy_pool.get_next_proxy()
    
    max_retries = 1
    if retries >= max_retries:
        logger.error(f"❌ Đã đạt số lần thử tối đa ({max_retries}) cho truy vấn: {query} với endpoint {endpoint}")
        return {
            "error": f"Đã đạt số lần thử tối đa ({max_retries}) cho truy vấn: {query}",
            "method": method
        }
    
    if method=='requests':
        if endpoint == "bing" or endpoint == "google":
            proxy = None
        logger.info(f"[REQUESTS] Đang dùng proxy: {proxy}")

        resp = search(query, 3, proxy=proxy, endpoint=endpoint)

        if resp is None:
            # logger.error(f"❌ Không nhận được phản hồi từ hàm `search` (resp is None). Endpoint: {endpoint}, Query: {query}")
            return {
                "error": "Không nhận được phản hồi từ công cụ tìm kiếm. Vui lòng kiểm tra kết nối mạng hoặc proxy.",
                "method": method
            }

        if not hasattr(resp, "text"):
            logger.error(f"❌ Phản hồi không chứa thuộc tính `text`: Kiểu dữ liệu nhận được: {type(resp)}. Endpoint: {endpoint}, Query: {query}")
            return {
                "error": f"Phản hồi không hợp lệ từ công cụ tìm kiếm ({type(resp)}).",
                "method": method
            }

        if hasattr(resp, "status_code") and resp.status_code != 200:
            logger.error(f"⚠️ HTTP status code trả về là {resp.status_code}. Endpoint: {endpoint}, Query: {query}")
            return {
                "error": f"Phản hồi HTTP không thành công. Mã lỗi: {resp.status_code}",
                "method": method
            }
        
        # logger.info(f"resp.text {resp.text}...")  # Log first 200 characters of the response text
        if endpoint == "google":
            detected = chardet.detect(resp.content)
            encoding = detected['encoding'] or 'utf-8'
            html_content = resp.content.decode(encoding, errors='ignore')
        else:
            html_content = resp.text

        soup = BeautifulSoup(html_content, "html.parser")

        # logger.info(f"soup: {soup}")
        if not soup:
            logger.error("Không thể phân tích cú pháp HTML")
            
        try:
            if endpoint == "mullvad leta":
                result_block = soup.find_all("article", class_='svelte-fmlk7p') 
            elif endpoint == "aol":
                result_block = soup.select("div.dd.algo.algo-sr.Sr, div.dd.algo.algo-sr.fst.Sr")
            elif endpoint == "duckduckgo":
                parent = soup.find("body")
                result_block = parent.select("table:nth-of-type("+str(3)+")")
            elif endpoint == "yahoo":
                result_block = soup.find_all("div", class_="dd algo algo-sr relsrch Sr")
            elif endpoint == "brave":
                result_block = soup.find_all("div", class_="snippet svelte-1o29vmf")
            elif endpoint == "bing":
                result_block = soup.find_all("li", class_="b_algo")
            elif endpoint == "google":
                result_block = soup.find_all("div", class_="ezO2md")
                # logger.info(f"result_block: {result_block}")
        except Exception as e:
            logger.error(f"❌ Lỗi khi tìm kiếm kết quả {endpoint} - {query}: {e}")
            with open("google.html", "w", encoding="utf-8") as f:
                f.write(resp.text)

        if len(result_block)<1:
            logger.error(f"Không tìm thấy kết quả trong HTML. Endpoint: {endpoint}, Query: {query}")
        
    else:
        # rand = random.randint(0,1)
        # if rand==1:
        #     domain="google"
        # else:
        #     domain="luxirty" 
        domain="searxng"
                   
        # print("domain:", domain)
        # s = GoogleSearcher(use_proxy_fingerprint=True)
        # resp = await s.get_html(query, save_to_file=True, domain=domain)
        
        # searcher = None
        
        # if domain == "luxirty":
        # if not app.state.search_instance._browser:
        #     await app.state.search_instance.init_browser()

        # if not app.state.search_instance._context:
        #     await app.state.search_instance._create_context()
                
        # searcher = app.state.luxirty_instance
        
        resp = await request.app.state.search_instance.get_html(query, save_to_file=True, domain=domain)
        # else:
        #     # if not app.state.google_instance._browser:
        #     #     await app.state.google_instance.init_browser()
                
        #     # searcher = app.state.google_instance
                
        #     resp = await request.app.state.google_instance.get_html(query, save_to_file=True, domain=domain)
        
        if not resp or not hasattr(resp, "html"):
            return {"error": "Phản hồi từ hàm search không hợp lệ"}
        soup = BeautifulSoup(resp.html, "html.parser")
        # if domain == "google":
        #     result_block = soup.find_all("div", class_="N54PNb BToiNc")
        #     if not result_block:
        #         result_block = soup.find_all("div", class_="wHYlTd Ww4FFb vt6azd tF2Cxc asEBEc")                

        # else:
        #     result_block = soup.find_all("div", class_="gsc-webResult gsc-result")   

        result_block = soup.find_all("article", class_="result result-default category-general")   

        if not result_block:
            logger.error("Không tìm thấy kết quả trong HTML")
            return {"error": "Không tìm thấy kết quả trong HTML"}
    # method = "fingerprint"
    # logger.info(f"Processing {len(result_block)} results using method: {method}")

    tasks = [process_result(result, method=method, endpoint=endpoint) for result in result_block]
    # print(tasks)
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.error(f"[Task {i}] Lỗi khi xử lý: {type(r).__name__} - {r}")
    except Exception as e:
        logger.exception("Lỗi khi chạy asyncio.gather:")
        return {"error": str(e)}

    # Lọc bỏ exception trước khi unpack
    valid_results = [
        (title, content)
        for r in results
        if not isinstance(r, Exception)
        and isinstance(r, tuple)
        and len(r) == 2
        for title, content in [r]
        if title and content
    ]

    # Gộp lại thành dict
    result = {title: content for title, content in valid_results}
    
    if len(result) == 0:
        import os
        from datetime import datetime
        logger.error("Không có kết quả hợp lệ sau khi lọc.")
        output_dir = "./google-search-html"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        sanitized_query = re.sub(r'[^a-zA-Z0-9]', '_', query)[:50]
        output_path = f"{output_dir}/{sanitized_query}-{timestamp}.html"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(resp.text)
        # with open("google.html", "w", encoding="utf-8") as f:
        #     f.write(resp.text)

        await search_response(query, request, method, endpoint, retries + 1)
    # result = {title: content for title, content in results if title and content}
    # print(result)
    return result

async def batch_search_fn(batch_inputs: List[Tuple[str, Request, str, str]]) -> List[dict]:

    tasks = [
        search_response(query, request, method, endpoint)
        for query, request, method, endpoint in batch_inputs
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)

# --------------Configs and dependencies--------------

@dataclass
class Config:
	port: int = 8080
	max_batch_size: int = 80

config = Config(
    port=8080,
    max_batch_size=80
)
 
# --------------Batcher Setup--------------

batcher = Batcher(
	batch_search_fn=batch_search_fn, 
	max_batch_size=config.max_batch_size
)
 

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/search")
async def query_result(req: Request):
    # body = await req.json()
    # query = body.get("query")
    endpoint = ""

    query = req.query_params.get("query")
    endpoint = req.query_params.get("endpoint")

    # If not in query params, try to get from JSON body
    if not query:
        try:
            body = await req.json()
            query = body.get("query")
            endpoint = body.get("endpoint", endpoint)
        except Exception:
            query = None
    
    print("📥 Query nhận được:", query)
        
    # domain="luxirty"
        
    # domain="google"
    # print("Query:", query)
    # result = await search_response(query, method="fingerprint", domain = domain)
    if endpoint == "" or endpoint is None:
        rand = random.randint(1,3)
        if rand==1:
            endpoint = "duckduckgo"
        elif rand==2:
            endpoint = "mullvad leta"
        elif rand==3:
            endpoint = "bing"
        # elif rand==4:
        #     endpoint = "google"

        # endpoint = "google"
        
    logger.info(f"Chạy tìm kiếm với endpoint: {endpoint} và query: {query}")
    try:
        result = await batcher.predict((query, req, "requests", endpoint))

        if isinstance(result, Exception):
            logger.error(f"Lỗi từ batcher.predict: {type(result).__name__} - {result}")
            return JSONResponse(status_code=500, content={"error": str(result)})

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        logger.exception("Lỗi trong query_result:")        
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Test
    
    # async def main_test():
    #     # async with lifespan(app): # Khởi tạo lifespan context để mở browser và context
    #         print("Running test search...")
    #         test_query = "Messi"
    #         # test_query = "chứng khoán hôm nay"
    #         result = await search_response(test_query) # Thử với method "requests"
    #         # result = await query_result(test_query) # Thử với method "fingerprint"
    #         print("\nTest Result:", result)

    # #         # for title, content in result.items():
    # #         #     print(f"Title: {title.splitlines()[0]}")
    # #         #     print(f"URL: {title.splitlines()[1]}")
    # #         #     print(f"Summary and Content: {content}\n")
    # #         # print("Test finished.")

    # asyncio.run(main_test())


