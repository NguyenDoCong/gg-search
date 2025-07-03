import random

# Định nghĩa các mối quan hệ hợp lệ (giữ nguyên như bạn đã có)
product_brand_map = {
    "điện thoại": ["Samsung", "Apple", "Xiaomi", "Oppo", "Vivo"],
    "laptop": ["Dell", "HP", "Asus", "Acer", "Lenovo", "MSI", "Apple"],
    "TV": ["Samsung", "LG", "Sony", "Panasonic"],
    "tủ lạnh": ["Samsung", "LG", "Panasonic", "Electrolux"],
    "máy giặt": ["Samsung", "LG", "Electrolux", "Panasonic"],
    "tai nghe": ["Sony", "JBL", "Logitech", "Apple", "Samsung"],
    "camera an ninh": ["Imou", "Ezviz", "Xiaomi", "Hikvision"],
    "máy in": ["Canon", "HP", "Brother", "Epson"],
    "bếp từ": ["Bosch", "Electrolux", "Hafele", "Teka"],
    "màn hình máy tính": ["Dell", "HP", "Asus", "Acer", "Samsung", "LG"],
    "máy ảnh": ["Canon", "Nikon", "Sony", "Fujifilm"] # Đảm bảo 'máy ảnh' có trong brand map nếu dùng chung product list
}

product_feature_map = {
    "điện thoại": ["5G", "camera", "pin trâu", "màn hình OLED", "sạc nhanh", "giá rẻ", "chụp ảnh đẹp", "gaming"],
    "laptop": ["gaming", "văn phòng", "học tập", "cấu hình cao", "SSD", "RAM 16GB", "màn hình cảm ứng"],
    "TV": ["4K", "OLED", "Smart TV", "8K", "HDR"],
    "tai nghe": ["chống ồn", "không dây", "Bluetooth", "over-ear", "in-ear"],
    "máy giặt": ["inverter", "cửa ngang", "cửa trên", "sấy"],
    "máy ảnh": ["DSLR", "Mirrorless", "zoom quang", "full-frame"],
    "màn hình máy tính": ["IPS", "144Hz", "27 inch", "ultrawide", "Full HD"],
}

specific_terms_by_product = {
    "điện thoại": ["Pro Max", "Ultra", "Plus", "mini", "Fold", "Flip", "128GB", "256GB", "512GB"],
    "laptop": ["i5", "i7", "Ryzen 5", "Ryzen 7", "RTX 3050", "RTX 4060", "GTX 1650", "DDR4", "DDR5", "SSD 512GB", "1TB SSD"],
}

locations = ["Hà Nội", "TP HCM", "Đà Nẵng", "Cần Thơ", "Hải Phòng"]
actions = ["mua", "bán", "đánh giá", "review", "so sánh", "giá", "cửa hàng"]
questions_starts = ["cách", "làm thế nào để", "ở đâu bán", "có nên mua"]
generic_features = ["giá rẻ", "cao cấp", "chính hãng", "mới nhất", "tốt nhất"]

def generate_meaningful_queries(num_queries=5000):
    queries = set()
    current_year = 2025

    # Lọc danh sách sản phẩm để đảm bảo chúng có mặt trong cả product_brand_map và product_feature_map
    # Điều này giúp tránh lỗi khi chọn sản phẩm không có thông tin brand hoặc feature
    common_products = list(set(product_brand_map.keys()) & set(product_feature_map.keys()))
    
    # Nếu bạn muốn tạo truy vấn từ tất cả các sản phẩm có trong product_brand_map,
    # hãy dùng product_for_template_1 = list(product_brand_map.keys())
    # Và xử lý các trường hợp không có feature map riêng
    product_for_template_1 = list(product_brand_map.keys())
    
    # Danh sách sản phẩm có thể có thương hiệu để dùng trong template 3 và 5
    products_with_brands = list(product_brand_map.keys())
    
    while len(queries) < num_queries:
        query_template_type = random.randint(1, 6)

        if query_template_type == 1:
            # Mẫu 1: [Product] [Brand] (Feature) (Specific Term) (Location)
            product = random.choice(product_for_template_1)
            brand = random.choice(product_brand_map[product])
            query_parts = [product, brand]

            if product in product_feature_map and random.random() < 0.6:
                query_parts.append(random.choice(product_feature_map[product]))
            if product in specific_terms_by_product and random.random() < 0.4:
                query_parts.append(random.choice(specific_terms_by_product[product]))
            if random.random() < 0.2:
                query_parts.append(random.choice(locations))
            queries.add(" ".join(query_parts).strip())

        elif query_template_type == 2:
            # Mẫu 2: [Action] [Product] [Brand] (Specific Term)
            action = random.choice(actions)
            product = random.choice(products_with_brands) # Chọn từ danh sách có brand
            brand = random.choice(product_brand_map[product])
            query_parts = [action, product, brand]
            if product in specific_terms_by_product and random.random() < 0.5:
                query_parts.append(random.choice(specific_terms_by_product[product]))
            queries.add(" ".join(query_parts).strip())

        elif query_template_type == 3:
            # Mẫu 3: [Question Start] [Product] (Brand) (Feature)
            question_start = random.choice(questions_starts)
            # Chọn sản phẩm từ danh sách có cả feature và brand (hoặc xử lý riêng nếu không có brand)
            product = random.choice(common_products) # Đảm bảo sản phẩm có cả brand và feature
            query_parts = [question_start, product]
            
            # Chỉ thêm brand nếu có trong product_brand_map và ngẫu nhiên
            if product in product_brand_map and random.random() < 0.5:
                brand_list = product_brand_map.get(product, [])
                if brand_list: # Kiểm tra list không rỗng
                    query_parts.append(random.choice(brand_list))
            
            # Chỉ thêm feature nếu có trong product_feature_map và ngẫu nhiên
            if product in product_feature_map and random.random() < 0.7:
                feature_list = product_feature_map.get(product, [])
                if feature_list: # Kiểm tra list không rỗng
                    query_parts.append(random.choice(feature_list))
            
            query = " ".join(query_parts).strip()
            queries.add(f"{query}?")

        elif query_template_type == 4:
            # Mẫu 4: So sánh (Product A Brand A vs Product B Brand B)
            # Đảm bảo chọn sản phẩm có brand
            product1 = random.choice(products_with_brands)
            brand1 = random.choice(product_brand_map[product1])
            
            product2 = random.choice(products_with_brands)
            brand2 = random.choice(product_brand_map[product2])
            
            compare_keyword = random.choice(["vs", "so sánh"])
            queries.add(f"{product1} {brand1} {compare_keyword} {product2} {brand2}".strip())
            
            if random.random() < 0.5:
                queries.add(f"so sánh {product1} và {product2}".strip())
            
            if random.random() < 0.3 and product1 in product_feature_map:
                 feat1 = random.choice(product_feature_map[product1])
                 queries.add(f"so sánh {product1} {feat1} và {product2}".strip())

        elif query_template_type == 5:
            # Mẫu 5: News/Event-related queries với năm hiện tại/sắp tới
            product = random.choice(products_with_brands) # Chọn từ danh sách có brand
            brand = random.choice(product_brand_map[product])
            news_type = random.choice(["review", "đánh giá", "tin tức", "rò rỉ", "khi nào ra mắt"])
            year_suffix = random.choice([str(current_year), str(current_year + 1)])
            queries.add(f"{news_type} {product} {brand} {year_suffix}".strip())
            if random.random() < 0.3:
                queries.add(f"cập nhật {product} {brand} {year_suffix}".strip())

        elif query_template_type == 6:
            # Mẫu 6: Product + Generic Feature (ví dụ: "điện thoại giá rẻ")
            product = random.choice(products_with_brands) # Chọn từ danh sách có brand
            feature = random.choice(generic_features)
            queries.add(f"{product} {feature}".strip())
            if random.random() < 0.4:
                brand = random.choice(product_brand_map[product])
                queries.add(f"{product} {brand} {feature}".strip())
    
    return list(queries)

all_meaningful_queries = generate_meaningful_queries(num_queries=5000)

print(f"Đã tạo {len(all_meaningful_queries)} truy vấn ý nghĩa hơn.")

# In thử một vài truy vấn đầu tiên
for i, q in enumerate(all_meaningful_queries[:20]):
    print(f"{i+1}. {q}")

# Lưu ra file
with open("meaningful_test_queries.txt", "w", encoding="utf-8") as f:
    for query in all_meaningful_queries:
        f.write(query + "\n")

print("Đã lưu các truy vấn ý nghĩa hơn vào file 'meaningful_test_queries.txt'")

if __name__ == "__main__":
    query = generate_meaningful_queries(num_queries=1)
    print("Generated query:", query)