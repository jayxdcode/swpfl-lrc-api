# swpfl-lrc-api

Simple FastAPI wrapper around the `syncedlyrics` package. It exposes a `/search` endpoint with multiple parameters to search lyrics.

This repo is intended to be deployed to Render (https://render.com).

## Endpoints

### `GET /`
Health check — returns `{ "status": "ok" }`

### `GET /search`
Search for lyrics.

#### Query Parameters
| Name | Type | Required | Description |
|------|------|-----------|-------------|
| `query` | `str` | ✅ | The song query to search for. |
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
curl "https://your-service.onrender.com/search?query=Mabataki%20Vaundy"

# Search with translation
curl "https://your-service.onrender.com/search?query=Mabataki%20Vaundy&trLang=en"

# Specify providers and enhanced search
curl "https://your-service.onrender.com/search?query=Mabataki%20Vaundy&providers=Musixmatch&providers=Lrclib&enhanced=true"
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
