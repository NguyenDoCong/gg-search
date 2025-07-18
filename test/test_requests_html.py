from requests_html import AsyncHTMLSession

asession = AsyncHTMLSession()

async def test():
    r = await asession.get('https://duckduckgo.com/?t=h_&q=vnz+h%C3%B4m+nay&ia=web')
    # await r.html.render()
    # about = r.html.find('#linktitle0', first=True)
    await r.html.arender(sleep=4)  # render JS với delay 2 giây

    # print("HTML content:", r.html.html)  # In ra nội dung HTML đã render

    with open("google.html", "w", encoding="utf-8") as f:
        f.write(r.html.html)

    # quotes = r.html.find("span.text")
    # for quote in quotes:
    #     print(quote.text)


if __name__ == "__main__":
    # import asyncio
    # asyncio.run(test())    
    asession.run(test)  # Chạy hàm test trong AsyncHTMLSession