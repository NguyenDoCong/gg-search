
import http from 'k6/http';
import { check, sleep } from 'k6';

const keywords = ["Bank", "Ng\u00e2n h\u00e0ng", "Vietcombank", "Credit", "Credit card", "Currency", "Exchange rate", "ATM", "\u0110\u1ea7u t\u01b0", "Investment", "Insurance", "Accounting", "Banking", "Stock", "Vietnam bank", "Euro", "Financial", "Tax", "USD", "Exchange rates", "Gold price", "FDI", "B\u1ea3o hi\u1ec3m", "Finance", "ANZ", "Prudential", "HSBC", "CC (c\u00f3 th\u1ec3 li\u00ean quan \u0111\u1ebfn Credit Card)", "Stock market", "Money", "Gold", "Rate", "United States Dollar", "Asia Commercial Bank (ACB)", "Vietnam Bank for Agriculture and Rural Development (Agribank)", "An Binh Commercial Joint Stock Bank", "VinaCapital", "Malaysian Ringgit", "Pound sterling", "Bank for Investment and Development of Vietnam (BIDV)", "MB Bank", "PT Bank Seabank Indonesia", "Standard Chartered", "Interest", "Interest rate", "Vietnam Export Import Commercial Joint Stock Bank (Eximbank)", "Prime rate", "Policy interest rate", "Ocean Bank", "Deposit account", "Personal income", "Income", "Vietinbank", "Foreign exchange", "Online banking", "Loan", "Vietnamese dong", "Invoice", "Australian Dollar", "Japanese Yen", "Chinese Yuan", "Bureau de change", "Mortgage loan", "Electronic funds transfer", "Citigroup", "Citibank", "Visa Electron", "Binance", "Home Credit Vi\u1ec7t Nam", "Wire transfer", "Discounts and allowances", "Credit history", "Tuition payments (li\u00ean quan \u0111\u1ebfn thanh to\u00e1n t\u00e0i ch\u00ednh)", "Chase Bank", "JPMorgan Chase & Co", "Bank card", "Electronic invoicing", "Siam Commercial Bank", "C\u00d4NG TY C\u1ed4 PH\u1ea6N T\u1eacP \u0110O\u00c0N V\u00c0NG B\u1ea0C \u0110\u00c1 QU\u00dd DOJI (DOJI Group)", "American Express", "Investing.com", "Visa", "MoMo", "VPBank", "TECHCOMBANK", "Sacombank", "Shinhan Bank America", "Tien Phong Commercial Joint Stock Bank", "Manulife", "Vietnam International Commercial Joint Stock Bank", "Bitcoin", "Financial transaction", "Tax deduction", "Revenue", "Business", "Indian Rupee", "Nigerian Naira", "Indonesian Rupiah"];

export let options = {
  vus: 80,
  duration: '60s',
};

export default function () {
  
  const url = 'http://127.0.0.1:8000/search';
  const keyword = keywords[Math.floor(Math.random() * keywords.length)];
  const payload = JSON.stringify({ query: keyword });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      timeout: '120s',
    },
  };

  const res = http.post(url, payload, params);

  // Luôn log lại keyword + status + response
  const bodyText = res && res.body ? res.body.substring(0, 200) : 'No body returned';
  console.log(`🔍 Keyword: ${keyword}`);
  console.log(`📦 Status: ${res.status}`);
  console.log(`📩 Body: ${bodyText}`);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}
