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
    app.state.search_instance = GoogleSearcher(use_proxy_fingerprint=True)
    
    # ✅ Gọi init_browser() sau khi khởi tạo
    await app.state.search_instance.init_browser()
    # # await app.state.google_instance.init_browser()   
    await app.state.search_instance._create_context()
    # # await app.state.google_instance._create_contexts(domain="google")

    proxy_ports = list(range(9050, 9130, 2))  # 9050 → 9088
    proxy_pool = ProxyPool()

    if not proxy_pool.redis.exists("tor:proxy_list"):
        proxy_pool.init_proxies(proxy_ports)
        logger.info(f"[INIT] ✅ Đã khởi tạo {len(proxy_ports)} proxy Tor vào Redis.")
    else:
        logger.info("[INIT] ♻️ Proxy list đã tồn tại trong Redis.")
    
    loop = asyncio.get_running_loop()
    task = asyncio.create_task(batcher.start(loop))
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

app = FastAPI(lifespan=lifespan)

# @cached(ttl=86400)  # Cache kết quả trong 1 giờ (3600 giây)
async def search_response(query, request: Request, method="fingerprint", endpoint="luxirty"):
    # global luxirty_instance, google_instance, search_count
    proxy_pool = ProxyPool()
    proxy = proxy_pool.get_next_proxy()
    
    if method=='requests':
        logger.info(f"[REQUESTS] Đang dùng proxy: {proxy}")

        resp = search(query, 5, proxy=proxy, endpoint=endpoint)
        if not resp or not hasattr(resp, "text"):
            logger.error("Phản hồi từ hàm search không hợp lệ")
            return {"error": "Phản hồi từ hàm search không hợp lệ", "method": method}
        soup = BeautifulSoup(resp.text, "html.parser")
        if not soup:
            logger.error("Không thể phân tích cú pháp HTML")
            
        if endpoint == "mullvad leta":
            result_block = soup.find_all("article", class_='svelte-fmlk7p') 
        elif endpoint == "gprivate":
            result_block = soup.find_all("div", class_='gsc-webResult gsc-result') 
        elif endpoint == "tiekoetter":
            result_block = soup.find_all("div", class_='gsc-webResult gsc-result') 
        elif endpoint == "yahoo":
            result_block = soup.find_all("div", class_="dd algo algo-sr relsrch Sr")

        # if len(result_block)<1:
        #     result_block = soup.find_all("div", class_="ezO2md")
        if len(result_block)<1:
            # print("Không tìm thấy kết quả trong HTML")
            logger.error("Không tìm thấy kết quả trong HTML")
        
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
    logger.info(f"Processing {len(result_block)} results using method: {method}")

    tasks = [process_result(result, method=method, endpoint=endpoint) for result in result_block[:3]]
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
	max_batch_size: int = 20

config = Config(
    port=8080,
    max_batch_size=20
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
    body = await req.json()
    query = body.get("query")
    print("📥 Query nhận được:", query)
        
    # domain="luxirty"
        
    # domain="google"
    # print("Query:", query)
    # result = await search_response(query, method="fingerprint", domain = domain)
    rand = random.randint(1,2)
    if rand==1:
        endpoint = "yahoo"
    else:
        endpoint = "mullvad leta"

    logger.info(f"Chạy tìm kiếm với endpoint: {endpoint}")
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


