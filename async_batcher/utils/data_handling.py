from urllib.parse import urlparse, parse_qs, unquote, urlencode, urlunparse
from search import GoogleSearcher
import logging
from requests import get
from bs4 import BeautifulSoup
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def process_result(result, method="requests", endpoint="luxirty"):

    # logger.info(f"Processing result with method: {result}")
    
    try:
        title_text = "Không có tiêu đề"
        summary_text = "Không có tóm tắt"

        if method=="requests":

            a = result.find("a", href=True)

            # link = result.a.get('href')
            link = a.get('href')

            logger.info(f"Link found: {link}")
            if not link:
                return None, None
            
            # print(f"link: {link}")

            # # Phân tích cú pháp URL
            # parsed_url = urlparse(link)
            # # Trích xuất tham số truy vấn
            # query_params = parse_qs(parsed_url.query)
            # # Lấy giá trị thực sự của URL
            # real_url = query_params.get('q', [None])[0]

            real_url = unquote(link)

            if not real_url:
                return None, None

            print("---------------------------")
            print(link)
            
            if endpoint == "mullvad leta":
                title = result.find("h3", class_="svelte-fmlk7p") 
                
            elif endpoint == "aol":
                title = result.find('a', class_="ac-algo fz-l ac-21th lh-24") 

            elif endpoint == "yahoo":
                title = result.find("h3", class_="title fc-2015C2-imp pt-6 ivmt-6 mxw-100p")

            elif endpoint == "duckduckgo":
                title = result.find("a", class_="result-link")
                real_url = unquote(link[25:-1])

                real_url = re.sub(r"&.*", "", real_url)

                print(f"real_url: {real_url}")

            elif endpoint == "brave":
                title = result.find("div", class_="title svelte-7ipt5e")

            elif endpoint == "bing":
                title = result.find("h2")

            # title = result.find("span", class_="CVA68e qXLe6d fuLhoc ZWRArf")

            if title:
                title_text = title.get_text(strip=True)

            else:
                title_text = "Không có tiêu đề"

            # print(title_text)

            if endpoint == "mullvad leta":
                summary = result.find("p", class_="result__body") 
            elif endpoint == "aol":       
                summary = result.find("p", class_="lh-16") 
            elif endpoint == "yahoo":
                summary = result.find("p", class_="fc-dustygray fz-14 lh-22 ls-02 mah-44 ov-h d-box fbox-ov fbox-lc2")
            elif endpoint == "duckduckgo":
                summary = result.find("td", class_="result-snippet")
            elif endpoint == "brave":
                summary = result.find("div", class_="snippet-content t-secondary svelte-9wfmiw")
            elif endpoint == "bing":
                summary = result.find("div", class_="b_caption")
       
            summary_text = summary.get_text(strip=True) if summary else "Không có tóm tắt"

            # print(summary_text)

        # else:
        #     print("Processing")
        #     link = result.find("a")
        #     if not link:
        #         print("Link not found")
        #         return None, None

        #     # Lấy giá trị thực sự của URL
        #     real_url = link.get('href')

        #     if not real_url:
        #         print("URL not found")
        #         return None, None

        #     # print("---------------------------")
        #     # print(link)
        #     if domain=="google":
        #         title = result.find("h3", class_="LC20lb MBeuO DKV0Md")
        #     else:
        #         # title = result.find("a", class_="gs-title")   
        #         # Lấy thẻ <a> trong <h3>
        #         title = result.find("h3").find("a")

        #     if title:
        #         title_text = title.get_text(strip=True)

        #     else:
        #         title_text = "Không có tiêu đề"

        #     # print(title_text)
        #     if domain=="google":
        #         summary = result.find("div", class_="VwiC3b yXK7lf p4wth r025kc hJNv6b Hdw6tb")
        #     else:
        #         # summary = result.find("div", class_="gs-bidi-start-align gs-snippet")
        #         summary = result.find("p", class_="content")            
                
        #     summary_text = summary.get_text(strip=True) if summary else "Không có tóm tắt"

        #     # print(summary_text)        

        content = ""

        if endpoint != "mullvad leta":
            # Chỉ lấy phần đầu của nội dung
            resp = get(real_url)
            soup = BeautifulSoup(resp.text, "html.parser")

            content = soup.get_text(separator="\n", strip=True)
            content = content[:1000]

        return title_text, summary_text + content    
    except Exception as e:
        logger.exception(f"Lỗi trong process_result: {e}")
        return None, None