# Deploy to Render

## One-click deploy via Render Blueprint

1. Go to https://dashboard.render.com
2. Click **New +** → **Blueprint**
3. Connect GitHub repo: `ssmurfgg04-gif/subdomain-enum-api`
4. Click **Apply**
5. Render reads `render.yaml` and auto-deploys

## Environment variables (set in Render dashboard)

| Variable | Value |
|---|---|
| `SUBDOMAINX_API_KEY` | Auto-generated (set a custom one for production) |
| `RAPIDAPI_KEY` | Your assigned RapidAPI provider key |
| `STRIPE_SECRET_KEY` | (optional) For direct billing |
| `STRIPE_WEBHOOK_SECRET` | (optional) For direct billing |

## Manual deploy via Docker (if Blueprint fails)

1. Create a new **Web Service**
2. Connect the GitHub repo
3. Render auto-detects the Dockerfile
4. Set the above env vars
5. Deploy

## Verify

```bash
curl https://subdomain-enum-api.onrender.com/v1/health
curl -H "x-rapidapi-key: YOUR_KEY" \
  -X POST https://subdomain-enum-api.onrender.com/v1/subdomain/scan \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com"}'
```
