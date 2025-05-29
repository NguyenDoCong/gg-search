from bs4 import BeautifulSoup
from __init__ import search
from urllib.parse import urlparse, parse_qs
import requests
import pprint
import re
from fastapi import FastAPI
import uvicorn

app = FastAPI()

def search_response(q="chứng khoán hôm nay"):
    resp = search(q)
    if not resp or not hasattr(resp, "text"):
        raise ValueError("Phản hồi từ hàm search không hợp lệ")
    # Parse
    soup = BeautifulSoup(resp.text, "html.parser")
    result_block = soup.find_all("div", class_="ezO2md")
    if not result_block:
        raise ValueError("Không tìm thấy kết quả trong HTML")
    
    result = []
    title_texts = []
    contents = []
    for result in result_block[:-1]:
        link = result.a.get('href')
        if not link:
            continue        
        # Phân tích cú pháp URL
        parsed_url = urlparse(link)
        # Trích xuất tham số truy vấn
        query_params = parse_qs(parsed_url.query)
        # Lấy giá trị thực sự của URL
        real_url = query_params.get('q', [None])[0]

        if not real_url:
            continue        

        title = result.find("span", class_="CVA68e qXLe6d fuLhoc ZWRArf")
        title_text = title.get_text(strip=True) if title else "Không có tiêu đề"
    
        summary = result.find("span", class_="qXLe6d FrIlee")
        summary_text = summary.get_text(strip=True) if summary else "Không có tóm tắt"

        try: 
            response = requests.get(real_url)
            response.raise_for_status()
            inner_soup = BeautifulSoup(response.text, "html.parser")
            text = inner_soup.get_text()
            text_no_breaks = text.strip().replace('\n', ' ')
            content = re.sub(r'\s{2,}', ' ', text_no_breaks)

            # print(repr(content))  
        except Exception as e:
            print("The error is: ",e)
            content = "Lỗi khi lấy nội dung"
        print(title_text)
        title_texts.append(title_text)
        contents.append(summary_text + "\n" + content)
    result = dict(zip(title_texts[:3], contents[:3]))

    return result
 

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/search")
def query_result(q: str = None):
    result = search_response(q)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)




