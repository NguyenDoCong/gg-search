
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 20,
  iterations: '5000',
};

export default function () {
  const url = 'http://127.0.0.1:8000/search';
  const payload = JSON.stringify({"query": "toto22"});

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(url, payload, params);

  console.log(`Status: ${res.status}, Body: ${res.body.substring(0, 100)}`);

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}
