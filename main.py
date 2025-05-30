from bs4 import BeautifulSoup
from __init__ import search
from urllib.parse import urlparse, parse_qs
import re
from fastapi import FastAPI
import uvicorn
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, Browser, BrowserContext
import asyncio
from aiocache import cached

app = FastAPI()

# Global variables for browser and context
browser: Browser = None
context: BrowserContext = None

@app.on_event("startup")
async def startup_event():
    global browser, context
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True, args=["--disable-extensions", "--disable-gpu", "--no-sandbox"])
    context = await browser.new_context(java_script_enabled=False,
                                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                                            viewport={"width": 800, "height": 600})

@app.on_event("shutdown")
async def shutdown_event():
    global browser, context
    if context:
        await context.close()
    if browser:
        await browser.close()

async def process_result(result):
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
    # print(real_url)

    title = result.find("span", class_="CVA68e qXLe6d fuLhoc ZWRArf")
    if title:
        title_text = title.get_text(strip=True)
    elif result.find(string="Tin bài hàng đầu"):
        title_text = result.find("span", class_="CVA68e qXLe6d").get_text(strip=True)
    else:
        title_text = "Không có tiêu đề"

    # print(title_text)

    summary = result.find("span", class_="qXLe6d FrIlee")
    summary_text = summary.get_text(strip=True) if summary else "Không có tóm tắt"

    # print(summary_text)

    try:
        global context
        page = await context.new_page()        

        async def block_resources(route):
            if route.request.resource_type in ["image", "font", "stylesheet", "media"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_resources)
        await page.goto(real_url, wait_until="domcontentloaded")

        # Lấy toàn bộ nội dung text của body
        body_text = await page.inner_text("body")
        body_text = body_text.replace('\n', ' ').replace('\t', ' ')
        content = re.sub(r'\s{2,}', ' ', body_text)

        await page.close()

        # print(content)
    except Exception as e:
        print("The error is: ", e)
        content = "Lỗi khi lấy nội dung"

    return title_text, summary_text + "\n" + content

@cached(ttl=1000)  # Cache kết quả trong 1 giờ (3600 giây)
async def search_response(query="chứng khoán hôm nay"):
    resp = search(query,3)
    if not resp or not hasattr(resp, "text"):
        return {"error": "Phản hồi từ hàm search không hợp lệ"}
    # Parse
    soup = BeautifulSoup(resp.text, "html.parser")
    result_block = soup.find_all("div", class_="ezO2md")
    if not result_block:
        return {"error": "Không tìm thấy kết quả trong HTML"}

    async with async_playwright() as p:
        # Chạy song song các tác vụ xử lý kết quả
        tasks = [process_result(result) for result in result_block[:3]]
        results = await asyncio.gather(*tasks)

    # Kết hợp tiêu đề và nội dung
    result = {title: content for title, content in results if title and content}
    print(result)
    return result
 

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/search")
async def query_result(query: str = None):
    result = await search_response(query)
    # return result
    return JSONResponse(status_code=200, content=result)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    # asyncio.run(search_response("chứng khoán hôm nay"))



