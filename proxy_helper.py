import random

PROXIES = [
    {
        "ip": "198.23.239.134",
        "port": "6540",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "city": "Buffalo",
        "country": "United States"
    },
    {
        "ip": "207.244.217.165",
        "port": "6712",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "hr-HR",
        "timezone_id": "Europe/Zagreb",
        "city": "Zagreb",
        "country": "Croatia"
    },
    {
        "ip": "107.172.163.27",
        "port": "6543",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/Chicago",
        "city": "Bloomingdale",
        "country": "United States"
    },
    {
        "ip": "23.94.138.75",
        "port": "6349",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "city": "Buffalo",
        "country": "United States"
    },
    {
        "ip": "216.10.27.159",
        "port": "6837",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/Chicago",
        "city": "Dallas",
        "country": "United States"
    },
    {
        "ip": "136.0.207.84",
        "port": "6661",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/Denver",
        "city": "Orem",
        "country": "United States"
    },
    {
        "ip": "64.64.118.149",
        "port": "6732",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "city": "Greenlawn",
        "country": "United States"
    },
    {
        "ip": "142.147.128.93",
        "port": "6593",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "city": "Ashburn",
        "country": "United States"
    },
    {
        "ip": "104.239.105.125",
        "port": "6655",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/Chicago",
        "city": "Dallas",
        "country": "United States"
    },
    {
        "ip": "173.0.9.70",
        "port": "5653",
        "user": "roedftzm",
        "pass": "4qcd5r6rcbqx",
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "city": "Ashburn",
        "country": "United States"
    }
]

def get_random_proxy():
    """Lấy 1 proxy ngẫu nhiên từ danh sách"""
    return random.choice(PROXIES)

def proxy_to_playwright_format(proxy):
    """Chuyển định dạng sang cho Playwright"""
    return {
        "server": f"http://{proxy['ip']}:{proxy['port']}",
        "username": proxy["user"],
        "password": proxy["pass"]
    }
