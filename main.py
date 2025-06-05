import random
from bs4 import BeautifulSoup
from __init__ import search
from search import GoogleSearcher
from urllib.parse import urlparse, parse_qs
import re
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, Browser, BrowserContext
import asyncio
from aiocache import cached

# Global variables for browser and context
browser: Browser = None
context: BrowserContext = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global browser, context, playwright_instance
    playwright_instance = await async_playwright().start()
    browser = await playwright_instance.chromium.launch(headless=True, args=["--disable-extensions", "--disable-gpu", "--no-sandbox"])
    context = await browser.new_context(
        java_script_enabled=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 800, "height": 600}
    )
    yield
    # Cleanup in reverse order
    if context:
        await context.close()
    if browser:
        await browser.close()
    if playwright_instance:
        await playwright_instance.stop()

app = FastAPI(lifespan=lifespan)

# app = FastAPI()

async def get_content(link):
    try:
        global context
        
        page = await context.new_page()        

        async def block_resources(route):
            if route.request.resource_type in ["image", "font", "stylesheet", "media"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_resources)
        await page.goto(link, wait_until="domcontentloaded", timeout=30000)

        # Lấy toàn bộ nội dung text của body
        body_text = await page.inner_text("body")
        body_text = body_text.replace('\n', ' ').replace('\t', ' ')
        content = re.sub(r'\s{2,}', ' ', body_text)

        # print(content)

        await page.close()


            # print(content)
    except Exception as e:
        print("The error is: ", e)
        content = "Lỗi khi lấy nội dung"
        await page.close()

    finally:
        if page:
            await page.close()
    return content

async def process_result(result, method="requests"):

    if method=="requests":
        link = result.a.get('href')
        if not link:
            return None, None

        # Phân tích cú pháp URL
        parsed_url = urlparse(link)
        # Trích xuất tham số truy vấn
        query_params = parse_qs(parsed_url.query)
        # Lấy giá trị thực sự của URL
        real_url = query_params.get('q', [None])[0]

        if not real_url:
            return None, None

        # print("---------------------------")
        # print(link)
        
        title = result.find("span", class_="CVA68e qXLe6d")

        # title = result.find("span", class_="CVA68e qXLe6d fuLhoc ZWRArf")
        # title = result.find("h3", class_="LC20lb MBeuO DKV0Md")

        if title:
            title_text = title.get_text(strip=True)

        else:
            title_text = "Không có tiêu đề"

        # print(title_text)

        summary = result.find("span", class_="qXLe6d FrIlee")
        # summary = result.find("div", class_="VwiC3b yXK7lf p4wth r025kc hJNv6b Hdw6tb")
        summary_text = summary.get_text(strip=True) if summary else "Không có tóm tắt"

        # print(summary_text)

    else:
        print("Processing")
        link = result.find("a")
        if not link:
            print("Link not found")
            return None, None

        # Lấy giá trị thực sự của URL
        real_url = link.get('href')

        if not real_url:
            print("URL not found")
            return None, None

        # print("---------------------------")
        print(link)
        
        title = result.find("h3", class_="LC20lb MBeuO DKV0Md")

        if title:
            title_text = title.get_text(strip=True)

        else:
            title_text = "Không có tiêu đề"

        print(title_text)

        summary = result.find("div", class_="VwiC3b yXK7lf p4wth r025kc hJNv6b Hdw6tb")
        summary_text = summary.get_text(strip=True) if summary else "Không có tóm tắt"

        print(summary_text)        

    content = await get_content(real_url)

    return title_text + '\n' + real_url, summary_text + '\n' + content

@cached(ttl=86400)  # Cache kết quả trong 1 giờ (3600 giây)
async def search_response(query="chứng khoán hôm nay", method="requests"):
    if method=='requests':
        resp = search(query,3)
        if not resp or not hasattr(resp, "text"):
            return {"error": "Phản hồi từ hàm search không hợp lệ"}
        soup = BeautifulSoup(resp.text, "html.parser")
        result_block = soup.find_all("table", class_='VeHcBf')
        if len(result_block)<1:
            result_block = soup.find_all("div", class_="ezO2md")
        # result_block = soup.find_all("div", class_="N54PNb BToiNc")
        method = "requests"
        
    else:
        s = GoogleSearcher()
        resp = await s.get_html("VN Index hôm nay")
        if not resp or not hasattr(resp, "html"):
            return {"error": "Phản hồi từ hàm search không hợp lệ"}
        soup = BeautifulSoup(resp.html, "html.parser")
        result_block = soup.find_all("div", class_="N54PNb BToiNc")
        method = "fingerprint"

    if not result_block:
        return {"error": "Không tìm thấy kết quả trong HTML"}

    tasks = [process_result(result, method=method) for result in result_block[:3]]
    # print(tasks)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # print(results)
    # Kết hợp tiêu đề và nội dung
    valid_results = [
        (title, content)
        for r in results
        if not isinstance(r, Exception) and r and isinstance(r, tuple) and len(r) == 2
        for title, content in [r]
        if title and content
    ]

    result = {title: content for title, content in valid_results if title and content}
    # print(result)
    return result
 

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/search")
async def query_result(query: str = None):
    rand = random.randint(1,2)
    if rand==1:
        method="requests"
    else:
        method="fingerprint"
    result = await search_response(query,method)
    # return result
    return JSONResponse(status_code=200, content=result)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

    # Test
    # async def main_test():
    #     async with lifespan(app): # Khởi tạo lifespan context để mở browser và context
    #         print("Running test search...")
    #         test_query = "VN Index hôm nay"
    #         # test_query = "chứng khoán hôm nay"
    #         # result = await search_response(test_query, method="requests") # Thử với method "requests"
    #         result = await search_response(test_query, method="fingerprint") # Thử với method "fingerprint"
    #         print("\nTest Result:")

    #         for title, content in result.items():
    #             print(f"Title: {title.splitlines()[0]}")
    #             print(f"URL: {title.splitlines()[1]}")
    #             print(f"Summary and Content: {content}\n")
    #         print("Test finished.")

    # asyncio.run(main_test())


