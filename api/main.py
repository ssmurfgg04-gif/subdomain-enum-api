import os
import time
import uuid
import hmac
import hashlib
from contextlib import asynccontextmanager

import httpx
import stripe
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import (
    SUBDOMAINX_URL,
    SUBDOMAINX_API_KEY,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    DIRECT_API_KEYS,
)
from .models import ScanRequest, ScanCreateResponse, ScanStatusResponse, HealthResponse

load_dotenv()

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

client = httpx.AsyncClient(base_url=SUBDOMAINX_URL, timeout=30.0)

DIRECT_USAGE: dict[str, int] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await client.aclose()


app = FastAPI(
    title="Subdomain Enumeration API",
    description="Enterprise-grade subdomain enumeration with active probing, tech fingerprinting, and takeover detection. Powered by SubdomainX + ProjectDiscovery toolchain.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_auth(
    request: Request,
    x_rapidapi_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    api_key = x_rapidapi_key
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if RAPIDAPI_KEY and api_key == RAPIDAPI_KEY:
        return api_key
    if DIRECT_API_KEYS and api_key in DIRECT_API_KEYS:
        DIRECT_USAGE[api_key] = DIRECT_USAGE.get(api_key, 0) + 1
        return api_key
    raise HTTPException(status_code=403, detail="Invalid API key")


def _subdomainx_headers() -> dict:
    return {
        "Authorization": f"Bearer {SUBDOMAINX_API_KEY}",
        "Content-Type": "application/json",
    }


@app.get("/v1/health", response_model=HealthResponse)
async def health():
    try:
        resp = await client.get("/api/health", headers=_subdomainx_headers())
        if resp.status_code == 200:
            data = resp.json()
            return HealthResponse(
                status="ok",
                version=data.get("version", "1.0.0"),
                uptime=data.get("uptime", "0s"),
                engine="subdomainx",
            )
    except Exception:
        pass
    return HealthResponse(
        status="degraded", version="1.0.0", uptime="0s", engine="subdomainx"
    )


@app.post(
    "/v1/subdomain/scan",
    response_model=ScanCreateResponse,
    summary="Start a subdomain scan",
    description="Start an asynchronous subdomain enumeration scan. Returns a scan_id immediately. Poll /v1/subdomain/scan/{scan_id} for results.",
)
async def create_scan(
    scan_req: ScanRequest,
    auth: str = Depends(verify_auth),
):
    payload = {
        "domain": scan_req.domain,
        "tools": scan_req.tools or ["subfinder", "crtsh"],
        "threads": scan_req.threads or 10,
        "retries": scan_req.retries or 3,
        "timeout": scan_req.timeout or 30,
        "rate_limit": scan_req.rate_limit or 100,
        "format": scan_req.format or "json",
        "options": {
            "httpx": True,
            "tech_detect": True,
            "takeover": True,
            **(scan_req.options or {}),
        },
    }
    resp = await client.post(
        "/api/scan", json=payload, headers=_subdomainx_headers()
    )
    if resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Scan engine error: {resp.text}",
        )
    data = resp.json()
    return ScanCreateResponse(
        scan_id=data.get("id", str(uuid.uuid4())),
        domain=scan_req.domain,
        status="queued",
        message="Scan started. Poll /v1/subdomain/scan/{scan_id} for results.",
    )


@app.get(
    "/v1/subdomain/scan/{scan_id}",
    response_model=ScanStatusResponse,
    summary="Get scan status and results",
    description="Poll this endpoint to get scan progress and final results.",
)
async def get_scan(
    scan_id: str,
    auth: str = Depends(verify_auth),
):
    resp = await client.get(
        f"/api/scan/{scan_id}", headers=_subdomainx_headers()
    )
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Scan not found")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Scan engine error: {resp.text}",
        )
    data = resp.json()
    return ScanStatusResponse(
        scan_id=data.get("id", scan_id),
        domain=data.get("domain", ""),
        status=data.get("status", "unknown"),
        progress=data.get("progress", 0),
        total_tools=data.get("total_tools", 0),
        completed_tools=data.get("completed_tools", 0),
        results=data.get("subdomains") or data.get("results"),
        error=data.get("error"),
    )


@app.get(
    "/v1/subdomain/scans",
    summary="List all scans",
    description="List all scans for this API key.",
)
async def list_scans(auth: str = Depends(verify_auth)):
    resp = await client.get("/api/scans", headers=_subdomainx_headers())
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Scan engine error: {resp.text}",
        )
    return resp.json()


@app.delete(
    "/v1/subdomain/scan/{scan_id}",
    summary="Cancel a running scan",
)
async def cancel_scan(
    scan_id: str,
    auth: str = Depends(verify_auth),
):
    resp = await client.delete(
        f"/api/scan/{scan_id}", headers=_subdomainx_headers()
    )
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Scan not found")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Scan engine error: {resp.text}",
        )
    return {"status": "cancelled", "scan_id": scan_id}


if STRIPE_SECRET_KEY:

    @app.post("/v1/stripe/webhook")
    async def stripe_webhook(request: Request):
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(status_code=400, detail="Invalid signature")

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            api_key = str(uuid.uuid4())[:16]
            DIRECT_API_KEYS.append(api_key)
            customer_email = session.get("customer_details", {}).get("email", "unknown")
            print(f"New subscriber: {customer_email}, API key: {api_key}")

        return {"received": True}


@app.get("/")
async def root():
    return {
        "api": "Subdomain Enumeration API",
        "version": "1.0.0",
        "endpoints": [
            "POST /v1/subdomain/scan",
            "GET  /v1/subdomain/scan/{scan_id}",
            "GET  /v1/subdomain/scans",
            "DELETE /v1/subdomain/scan/{scan_id}",
            "GET  /v1/health",
        ],
        "docs": "/docs",
    }
