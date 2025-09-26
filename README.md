# swpfl-lrc-api

Simple FastAPI wrapper around the `syncedlyrics` package. It exposes a `/search` endpoint with multiple parameters to search lyrics.

This repo is intended to be deployed to Render (https://render.com).

## 🚀 One-Click Deploy

Click the button below to deploy this API instantly on [Render](https://render.com):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fjayxdcode%2Fswpfl-lrc-api)

## Endpoints

### `GET /`
Health check — returns `{ "status": "ok" }`

### `GET /search`
Search for lyrics.

#### Query Parameters
| Name | Type | Required | Description |
|------|------|-----------|-------------|
| `q` | `str` | ✅ | The song query to search for. |
| `trLang` | `str` | ⛔ | ISO 639-1 translation language code (e.g., `en`, `fr`). |
| `providers` | `list[str]` | ⛔ | List of providers to query. Automatically chosen if not provided. |
| `synced` | `bool` | ⛔ | Whether to search for synced lyrics. Defaults to `True`. |
| `enhanced` | `bool` | ⛔ | Whether to search for word-level karaoke format (if not found, regular synced lyrics returned). Defaults to `False`. |

#### Available Providers
- `Musixmatch`
- `Lrclib`
- `NetEase`
- `Megalobiz`
- `Genius` *(Plain-only provider)*

> 💡 It is recommended **not** to specify providers manually — the API will pick the best ones automatically, especially when using `trLang`.

#### Example Requests
```bash
# Simple search
curl "https://your-service.onrender.com/search?q=Mabataki%20Vaundy"

# Search with translation
curl "https://your-service.onrender.com/search?q=Mabataki%20Vaundy&trLang=en"

# Specify providers and enhanced search
curl "https://your-service.onrender.com/search?q=Mabataki%20Vaundy&providers=Musixmatch&providers=Lrclib&enhanced=true"
```

#### Example Response
```json
{
  "query": "Mabataki  Vaundy",
  "trLang": "en",
  "providers": ["Musixmatch", "Lrclib"],
  "synced": true,
  "enhanced": true,
  "lrc": "[00:00.00] Sample lyric line ..."
}
```

## 🧰 Modules Used

This project wouldn’t be possible without these amazing open-source libraries:

- [**FastAPI**](https://fastapi.tiangolo.com/) — for building the web API quickly and efficiently.
- [**Uvicorn**](https://www.uvicorn.org/) — lightning-fast ASGI server to run the FastAPI app.
- [**HTTPX**](https://www.python-httpx.org/) — modern async HTTP client used for self-pinging.
- [**syncedlyrics**](https://pypi.org/project/syncedlyrics/) — the core library that powers lyric searches across multiple providers.

🙏 Huge thanks to the developers and contributors of these tools!
