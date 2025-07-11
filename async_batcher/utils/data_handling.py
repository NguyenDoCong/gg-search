from urllib.parse import urlparse, parse_qs
from search import GoogleSearcher

async def process_result(result, method="requests", domain="luxirty", searcher: GoogleSearcher = None):

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
        # print(link)
        if domain=="google":
            title = result.find("h3", class_="LC20lb MBeuO DKV0Md")
        else:
            title = result.find("a", class_="gs-title")       

        if title:
            title_text = title.get_text(strip=True)

        else:
            title_text = "Không có tiêu đề"

        # print(title_text)
        if domain=="google":
            summary = result.find("div", class_="VwiC3b yXK7lf p4wth r025kc hJNv6b Hdw6tb")
        else:
            summary = result.find("div", class_="gs-bidi-start-align gs-snippet")
            
        summary_text = summary.get_text(strip=True) if summary else "Không có tóm tắt"

        # print(summary_text)        

    # content = await searcher.get_content(real_url)
    content = ""

    return title_text, summary_text + content    