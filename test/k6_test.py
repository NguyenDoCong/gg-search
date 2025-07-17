import subprocess
import json

keywords = []
with open("test/keywords.txt", "r", encoding="utf-8") as file:
    keywords = [line.strip() for line in file if line.strip()]

# ✅ Tham số truyền vào
url = "http://127.0.0.1:8000/search"
vus = 1
# duration = '60s'
iterations = 1

# ✅ Chuyển danh sách từ khóa sang JS array
js_keywords = json.dumps(keywords)

# ✅ Tạo nội dung file test.js bằng f-string
js_script = f"""
import http from 'k6/http';
import {{ check, sleep }} from 'k6';

const keywords = {js_keywords};

export let options = {{
  vus: {vus},
  iterations: '{iterations}',
}};

export default function () {{
  
  const url = '{url}';
  const keyword = keywords[Math.floor(Math.random() * keywords.length)];
  const payload = JSON.stringify({{ query: keyword }});
  
  const params = {{
    headers: {{
      'Content-Type': 'application/json',
      timeout: '120s',
    }},
  }};

  const res = http.post(url, payload, params);

  // Luôn log lại keyword + status + response
  const bodyText = res && res.body ? res.body.substring(0, 200) : 'No body returned';
  console.log(`🔍 Keyword: ${{keyword}}`);
  console.log(`📦 Status: ${{res.status}}`);
  console.log(`📩 Body: ${{bodyText}}`);
  
  check(res, {{
    'status is 200': (r) => r.status === 200,
  }});

  sleep(1);
}}
"""

# Ghi file test.js
with open("test/test.js", "w", encoding="utf-8") as f:
    f.write(js_script)

# Chạy K6 và ghi log
print("🔄 Running k6 with random keyword per iteration...")
with open("test/log_responses.txt", "w") as log_file:
    subprocess.run(["k6", "run", "test/test.js"], stdout=log_file, stderr=subprocess.STDOUT)

print("✅ Kết thúc test. Log đã ghi vào log_responses.txt")
