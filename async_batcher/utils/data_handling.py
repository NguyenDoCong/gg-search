from urllib.parse import urlparse, parse_qs
from search import GoogleSearcher
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

async def process_result(result, method="requests", endpoint="luxirty"):

    # logger.info(f"Processing result with method: {result}")
    
    try:
        title_text = "Không có tiêu đề"
        summary_text = "Không có tóm tắt"

        if method=="requests":

            # link = result.a.get('href')
            # if not link:
            #     return None, None

            # # Phân tích cú pháp URL
            # parsed_url = urlparse(link)
            # # Trích xuất tham số truy vấn
            # query_params = parse_qs(parsed_url.query)
            # # Lấy giá trị thực sự của URL
            # real_url = query_params.get('q', [None])[0]

            # if not real_url:
            #     return None, None

            # print("---------------------------")
            # print(link)
            
            if endpoint == "mullvad leta":
                title = result.find("h3", class_="svelte-fmlk7p") 
                
            elif endpoint == "gprivate":
                title = result.findAll('a', id=lambda x: x and x.startswith('linktitle')) 

            elif endpoint == "yahoo":
                title = result.find("h3", class_="title fc-2015C2-imp pt-6 ivmt-6 mxw-100p")


            # title = result.find("span", class_="CVA68e qXLe6d fuLhoc ZWRArf")

            if title:
                title_text = title.get_text(strip=True)

            else:
                title_text = "Không có tiêu đề"

            # print(title_text)

            if endpoint == "mullvad leta":
                summary = result.find("p", class_="result__body") 
            elif endpoint == "gprivate":       
                summary = result.find("div", class_="gs-bidi-start-align gs-snippet") 
            elif endpoint == "yahoo":
                summary = result.find("p", class_="fc-dustygray fz-14 lh-22 ls-02 mah-44 ov-h d-box fbox-ov fbox-lc2")
       
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

        # content = await searcher.get_content(real_url)
        content = ""

        return title_text, summary_text + content    
    except Exception as e:
        logger.exception("Lỗi trong process_result:")
        return None, None