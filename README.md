# Subdomain Enumeration API

Enterprise-grade subdomain enumeration, HTTP probing, tech fingerprinting, and takeover detection via a simple REST API.

## Features

- Passive subdomain enumeration (subfinder, crtsh, wayback, etc.)
- Active HTTP probing (status codes, titles, content-length, webserver)
- Technology fingerprinting (frameworks, languages, analytics, CDN)
- Subdomain takeover detection via nuclei templates
- Asynchronous scanning — submit a domain, poll for results

## Quick Start

```bash
# Submit a domain for scanning
curl -X POST https://subdomain-enum-api.up.railway.app/v1/subdomain/scan \
  -H "x-rapidapi-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "tools": ["subfinder", "crtsh"]}'

# Poll for results
curl https://subdomain-enum-api.up.railway.app/v1/subdomain/scan/SCAN_ID \
  -H "x-rapidapi-key: YOUR_API_KEY"
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/subdomain/scan` | Start a new subdomain scan |
| GET | `/v1/subdomain/scan/{id}` | Get scan status and results |
| GET | `/v1/subdomain/scans` | List all scans |
| DELETE | `/v1/subdomain/scan/{id}` | Cancel a running scan |
| GET | `/v1/health` | Health check |

## Pricing

| Tier | Price | Requests/Month |
|------|-------|----------------|
| Free | $0 | 50 (rate-limited) |
| Basic | $5 | 500 |
| Pro | $20 | 5,000 |
| Ultra | $50 | 50,000 |

## Tech Stack

- **API**: FastAPI (Python), Uvicorn
- **Scanner**: SubdomainX + subfinder + httpx + nuclei
- **Deployment**: Docker on Railway (always-on, no sleep)
- **Auth**: RapidAPI key validation

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
subdomainx serve --port 8080 --api-key dev-key &
uvicorn api.main:app --reload
```
