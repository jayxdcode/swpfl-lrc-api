from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import os
import asyncio
import httpx
import re

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
	translated: Optional[bool] = False
	v2: Optional[dict] = None


@app.get("/")
async def root():
	return {"status": "ok"}


@app.get("/search", response_model=SearchResult)
async def search(
	q: Optional[str] = Query(None, description="The song query to search for."),
	trLang: Optional[str] = Query(None, description="ISO 639-1 translation language code (e.g., 'en', 'fr')."),
	providers: Optional[List[str]] = Query(None, description="List of providers to query. Automatically chosen if not provided."),
	synced: Optional[bool] = Query(True, description="Whether to search for synced lyrics (default True)."),
	enhanced: Optional[bool] = Query(False, description="Whether to search for word-level karaoke format (default False).")
):
	"""
	Search lyrics using syncedlyrics CLI with verbose logs.
	Includes fallback for translation failure, structured outputs, and provider detection.
	"""

	# 🧱 1. Validate query
	if not q:
		raise HTTPException(status_code=422, detail={
			"error": "Missing required query parameter 'q'.",
			"required_params": ["q {str}"],
			"optional_params": ["trLang {str, ISO 639-1 code}", "providers {list[str]}", "synced {bool}", "enhanced {bool}"]
		})

	async def run_cli(query: str, lang: Optional[str] = None):
		cmd = ["syncedlyrics", "-v", query]
		if lang:
			cmd += ["--lang", lang]
		if providers:
			for p in providers:
				cmd += ["--provider", p]
		if synced:
			cmd += ["--synced-only"]
		else:
			cmd += ["--plain-only"]
		if enhanced:
			cmd += ["--enhanced"]

		process = await asyncio.create_subprocess_exec(
			*cmd,
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE
		)
		stdout, stderr = await process.communicate()
		stdout_text = stdout.decode().strip()
		stderr_text = stderr.decode().strip()

		# 🔍 print to console for monitoring
		if stderr_text:
			print(f"[syncedlyrics -v logs for '{query}']:\n{stderr_text}")

		return stdout_text, stderr_text

	# 🌀 2. Try with translation first (if supplied)
	stdout_text = ""
	stderr_text = ""
	if trLang:
		stdout_text, stderr_text = await run_cli(q, trLang)
		if not stdout_text:
			print(f"[fallback] No results with translation '{trLang}', retrying without translation...")
			stdout_text, stderr_text = await run_cli(q)
	else:
		stdout_text, stderr_text = await run_cli(q)

	if not stdout_text:
		raise HTTPException(status_code=404, detail=f"No lyrics found for '{q}'")

	# 🧠 3. Extract provider info from logs
	provider_logs = re.findall(r"(DEBUG|INFO):syncedlyrics:[^\n]+", stderr_text)
	used_provider = None
	for line in stderr_text.splitlines():
		if "Lyrics found for" in line:
			match = re.search(r'on (\w+)', line)
			if match:
				used_provider = match.group(1)
				break

	# 🈶 4. Parse translations
	lines = stdout_text.splitlines()
	translated = any(re.search(r"^\(.*\)$", line.strip()) for line in lines)
	if translated and not used_provider:
		used_provider = "Musixmatch"  # only Musixmatch has translations

	# 🧩 5. Build v2 breakdowns
	syncedLrc = []
	plainLyrics = []
	syncedTr = []
	plainTr = []

	prev_time = None
	for line in lines:
		line = line.strip()
		# detect synced line
		time_match = re.match(r"^\[(.*?)\]\s*(.*)", line)
		if time_match:
			prev_time = time_match.group(1)
			text = time_match.group(2)
			syncedLrc.append(f"[{prev_time}] {text}")
			plainLyrics.append(text)
		elif re.match(r"^\(.*\)$", line):
			tr_text = line.strip("()")
			if prev_time:
				syncedTr.append(f"[{prev_time}] {tr_text}")
			plainTr.append(tr_text)

	v2 = {
		"syncedLrc": syncedLrc or None,
		"plainLyrics": plainLyrics or None,
		"syncedTr": syncedTr or None,
		"plainTr": plainTr or None,
	}

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
		"translated": translated,
		"v2": v2
	}


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