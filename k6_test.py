import subprocess
import json
from search_keywords import keywords
import random

random_keyword = random.choice(keywords)
print(random_keyword)

# ✅ Tham số truyền vào
url = "http://127.0.0.1:8000/search"
payload = {
    "query": random_keyword
}
vus = 20
iterations = 5000

# ✅ Tạo nội dung file test.js bằng f-string
js_script = f"""
import http from 'k6/http';
import {{ check, sleep }} from 'k6';

export let options = {{
  vus: {vus},
  iterations: '{iterations}',
}};

export default function () {{
  const url = '{url}';
  const payload = JSON.stringify({json.dumps(payload)});

  const params = {{
    headers: {{
      'Content-Type': 'application/json',
    }},
  }};

  const res = http.post(url, payload, params);

  console.log(`Status: ${{res.status}}, Body: ${{res.body.substring(0, 100)}}`);

  check(res, {{
    'status is 200': (r) => r.status === 200,
  }});

  sleep(1);
}}
"""

# Ghi file test.js
with open('test.js', 'w') as f:
    f.write(js_script)

# Chạy k6 và lưu stdout
print("🔄 Đang chạy K6 POST test...")
result = subprocess.run(['k6', 'run', 'test.js'], capture_output=True, text=True)

# Ghi log ra file log.txt
with open('log.txt', 'w') as log_file:
    log_file.write(result.stdout)

print("✅ Kết thúc test. Log đã ghi vào file: log.txt")
