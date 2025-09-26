from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import os
import asyncio
import httpx
import re
import json

app = FastAPI()

class SearchResult(BaseModel):
	query: str
	trLang: Optional[str] = None
	providers: Optional[List[str]] = None
	synced: Optional[bool] = True
	enhanced: Optional[bool] = False
	lrc: Optional[str] = None
	used_provider: Optional[str] = None
	provider_logs: Optional[List[str]] = None


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
	"""
	Search using syncedlyrics CLI with verbose (-v) logs internally to detect which provider worked.
	Example: GET /search?q=Mabataki%20Vaundy
	"""
	try:
		# Build CLI command
		cmd = ["syncedlyrics", "-v", q]
		
		if trLang:
			cmd += ["--lang", trLang]
		if providers:
			for p in providers:
				cmd += ["--provider", p]
		if synced:
			cmd += ["--synced-only"]
		else:
			cmd += ["--plain-only"]
		if enhanced:
			cmd += ["--enhanced"]

		# Run subprocess silently but capture logs
		process = await asyncio.create_subprocess_exec(
			*cmd,
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE
		)

		stdout, stderr = await process.communicate()

		stdout_text = stdout.decode().strip()
		stderr_text = stderr.decode().strip()

		# Extract provider logs
		provider_logs = re.findall(r"(DEBUG|INFO):syncedlyrics:[^\n]+", stderr_text)
		used_provider = None
		for line in provider_logs:
			if "Lyrics found for" in line:
				match = re.search(r'on (\w+)', line)
				if match:
					used_provider = match.group(1)

		# Handle failure
		if not stdout_text:
			raise Exception("No lyrics found or CLI failed.")

		return {
			"status": 200,
			"query": q,
			"trLang": trLang,
			"providers": providers,
			"synced": bool(re.search(r"\[\d.*?\]", stdout_text)),
			"enhanced": bool(re.search(r"\<\d.*?\>", stdout_text)),
			"lrc": stdout_text,
			"used_provider": used_provider,
			"provider_logs": provider_logs,
		}

	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get("/_ping")
async def ping():
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
