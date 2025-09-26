from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import os
import asyncio
import httpx
import syncedlyrics

app = FastAPI()

class SearchResult(BaseModel):
	query: str
	trLang: Optional[str] = None
	providers: Optional[List[str]] = None
	synced: Optional[bool] = True
	enhanced: Optional[bool] = False
	lrc: object | None


@app.get("/")
async def root():
	return {"status": "ok"}


@app.get("/search", response_model=SearchResult)
async def search(
	q: str = Query(..., description="The song query to search for."),
	trLang: Optional[str] = Query(None, description="ISO 639-1 translation language code (e.g., 'en', 'fr')."),
	providers: Optional[List[str]] = Query(None, description="List of providers to query. Automatically chosen if not provided."),
	synced: Optional[bool] = Query(True, description="Whether to search for synced lyrics (default True)."),
	enhanced: Optional[bool] = Query(False, description="Whether to search for word-level karaoke format (default False).")
):
	"""Search syncedlyrics for `query` and return the raw result.
	Example: GET /search?query=Mabataki%20Vaundy&trLang=en&providers=Musixmatch&enhanced=true
	"""
	try:
		lrc = syncedlyrics.search(
	        q,
		    lang=trLang,
		    providers=providers
			synced-only=True
			enhanced=enhanced
		) if synced else syncedlyrics.search(
			q,
			lang=trLang,
			providers=providers,
			plain-only=True,
		    enhanced=enhanced
		)
		return {
			"status": 200,
			"query": query,
			"trLang": trLang,
			"providers": providers,
			"synced": synced,
			"enhanced": enhanced,
			"lrc": lrc,
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get("/_ping")
async def ping():
	"""Simple health endpoint used by the self-pinger and external checks."""
	return {"pong": True}


async def _self_pinger_loop():
	service_url = os.getenv("SERVICE_URL")
	if not service_url:
		return

	service_url = service_url.rstrip("/") + "/_ping"
	interval = int(os.getenv("SELF_PING_INTERVAL", "300"))

	async with httpx.AsyncClient() as client:
		while True:
			try:
				resp = await client.get(service_url, timeout=10.0)
				print(f"[self-pinger] pinged {service_url} status={resp.status_code}")
			except Exception as ex:
				print(f"[self-pinger] ping failed: {ex}")
			await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_event():
	asyncio.create_task(_self_pinger_loop())


if __name__ == "__main__":
	import uvicorn
	uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
