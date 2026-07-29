import os
from dotenv import load_dotenv

load_dotenv()

SUBDOMAINX_URL = os.getenv("SUBDOMAINX_URL", "http://127.0.0.1:8080")
SUBDOMAINX_API_KEY = os.getenv("SUBDOMAINX_API_KEY", "dev-key-change-me")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

raw_keys = os.getenv("DIRECT_API_KEYS", "")
DIRECT_API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]
