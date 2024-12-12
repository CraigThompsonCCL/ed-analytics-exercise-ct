import httpx
import os
from dotenv import load_dotenv

load_dotenv()

if github_token := os.getenv("GITHUB_ACCESS_TOKEN"):
    async_client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {github_token}",
        }
    )
else:
    async_client = httpx.AsyncClient()
