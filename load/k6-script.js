import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics to measure throughput and failure rates under load
export const complaintSubmissions = new Counter('complaints_submitted');
export const rateLimitHits = new Counter('rate_limit_hits_429');
export const errorRate = new Rate('error_rate');
export const complaintLatency = new Trend('complaint_post_latency_ms');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Realistic bilingual and Roman Urdu complaints matching CivicPulse problem statement (§1.1)
const complaintsPool = [
  {
    text: "Pani ki main pipeline phat gayi hai street 12 mein, sadak par talaab ban chuka hai",
    location: "Block A, Street 12, Gulshan",
    reporter_contact: "citizen1@karachi.gov"
  },
  {
    text: "Bijli subah 6 bajay se gul hai poori colony mein, transformer jal gaya hai",
    location: "Sector 4, North Nazimabad",
    reporter_contact: "resident_nn@yahoo.com"
  },
  {
    text: "Gutter ka dhiakkan gayab hai school ke bahar, bacho ke girne ka shadeed khatra hai",
    location: "Opposite Govt Primary School, Street 4",
    reporter_contact: "school_head@edu.pk"
  },
  {
    text: "Solid waste garbage dump overflowing for 5 days, unbearable smell and disease outbreak risk",
    location: "Plot 45, Phase 2, Industrial Area",
    reporter_contact: "factory_sec@org.pk"
  },
  {
    text: "Street lights across entire lane broken since last month, multiple theft attempts reported",
    location: "Lane 7, DHA Phase 5",
    reporter_contact: "dha_watch@gmail.com"
  },
  {
    text: "Main road par barha gaddha ban chuka hai, motorbikes roz gir rahi hain",
    location: "Main Boulevard, near Civic Center",
    reporter_contact: "rider99@gmail.com"
  }
];

export const options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp up to 10 VUs
    { duration: '30s', target: 50 }, // Ramp up to 50 VUs (stress HPA threshold)
    { duration: '2m',  target: 50 }, // Sustained heavy load to trigger HPA scale-out
    { duration: '30s', target: 0 },  // Ramp down to observe cooldown/stabilization
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000'], // 95% of requests must complete within 1000ms
    'error_rate': ['rate<0.05'],         // Handled errors (excluding expected 429) < 5%
  },
};

export default function () {
  const payload = complaintsPool[Math.floor(Math.random() * complaintsPool.length)];
  const headers = {
    'Content-Type': 'application/json',
    'X-Forwarded-For': `192.168.1.${Math.floor(Math.random() * 250) + 1}`, // Simulate diverse IPs to test rate limiting (§3.2)
  };

  // 1. Submit complaint (POST /api/complaints)
  const postStart = Date.now();
  const postRes = http.post(`${BASE_URL}/api/complaints`, JSON.stringify(payload), { headers });
  complaintLatency.add(Date.now() - postStart);

  const postSuccess = check(postRes, {
    'POST status is 201 (Created) or 429 (Rate Limited)': (r) => r.status === 201 || r.status === 429,
  });

  if (postRes.status === 201) {
    complaintSubmissions.add(1);
    errorRate.add(0);
  } else if (postRes.status === 429) {
    rateLimitHits.add(1);
    errorRate.add(0); // 429 is expected and handled under rate limiting
  } else {
    errorRate.add(1);
  }

  // 2. Fetch list of complaints (GET /api/complaints)
  const getRes = http.get(`${BASE_URL}/api/complaints?page=1&page_size=10`, { headers });
  const getSuccess = check(getRes, {
    'GET /api/complaints is 200': (r) => r.status === 200,
  });
  if (!getSuccess) {
    errorRate.add(1);
  }

  // 3. Fetch summary stats with Redis cache (GET /api/stats)
  const statsRes = http.get(`${BASE_URL}/api/stats`, { headers });
  check(statsRes, {
    'GET /api/stats is 200': (r) => r.status === 200,
    'Stats response has X-Cache header': (r) => r.headers['X-Cache'] !== undefined || r.headers['x-cache'] !== undefined,
  });

  // Short pacing sleep between citizen actions
  sleep(0.3 + Math.random() * 0.4);
}
