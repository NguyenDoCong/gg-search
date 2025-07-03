import random

def gen_queries(num_queries):
    topics = [
        "du lịch", "ẩm thực", "công nghệ", "giáo dục", "sức khỏe", "tài chính", "thời trang",
        "điện thoại", "làm đẹp", "thể thao", "game", "âm nhạc", "phim ảnh", "xe cộ", "mẹ và bé"
    ]

    phrases = [
        "làm sao để {} hiệu quả",
        "bí quyết {} nhanh chóng",
        "kinh nghiệm {} cho người mới",
        "top 10 mẹo {} bạn nên biết",
        "{} là gì?",
        "hướng dẫn {} từng bước",
        "cách {} an toàn tại nhà",
        "tại sao nên {} thường xuyên",
        "những lưu ý khi {}",
        "địa điểm {} nổi tiếng ở Việt Nam",
        "nên {} vào thời điểm nào",
        "giá {} hiện nay là bao nhiêu",
        "review sản phẩm liên quan đến {}",
        "so sánh các cách {} phổ biến",
        "xu hướng {} năm 2025",
    ]

    keywords = set()
    while len(keywords) < num_queries:
        topic = random.choice(topics)
        phrase = random.choice(phrases)
        keywords.add(phrase.format(topic))

    # Lưu vào file Python
    with open("keywords_list.py", "w", encoding="utf-8") as f:
        f.write("keywords = [\n")
        for kw in sorted(keywords):
            f.write(f"    \"{kw}\",\n")
        f.write("]\n")
        
if __name__ == "__main__":
    gen_queries(5000)        
    
