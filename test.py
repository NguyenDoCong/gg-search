from bs4 import BeautifulSoup

with open("tmp.html", "r") as f:
    content = f.read()
    soup = BeautifulSoup(content, "html.parser")    
    result = soup.find("a", href=True)
    link = result.get('href') if result else None
    print(link)