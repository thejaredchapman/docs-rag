# Web UI -- `app.py`

**Yes, this is the frontend interface.** `app.py` is a Flask server that
serves both a browser-based search UI (`templates/index.html` +
`static/app.js` + `static/style.css`) and a JSON API that the UI calls.
LLM calls happen server-side only -- your provider API key never reaches
the browser.

## Prerequisites

- Python 3.10+, dependencies installed, `.env` configured (same as the
  [root README](README.md))
- An index already built: `python ingest.py`

## Running it

```bash
source venv/bin/activate
python app.py
```

```
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5050
```

Open **http://localhost:5050** in a browser. You'll see:

- A title (`Ask the Docs`) and a single search box with an "Ask" button.
- A status line below the box (`Thinking...` while waiting, `(answered
  from cache)` if the similarity cache served the answer, or an error
  message if something went wrong).
- The answer, rendered as sanitized Markdown (headings, code blocks with
  syntax highlighting via `highlight.js`, lists, etc.).
- A bulleted list of source files under the answer.

Type a question, hit Enter or click Ask, and the page calls `POST
/api/ask` via `fetch()` and renders the JSON response. No page reload.

Change the port with `FLASK_PORT` in `.env` (default `5050`).

## Frontend stack

| Piece | Role |
|---|---|
| `templates/index.html` | The page skeleton: search form, answer container, sources list |
| `static/style.css` | Minimal styling, no framework |
| `static/app.js` | Fetches `/api/ask`, renders the response |
| `marked.js` (CDN) | Parses the answer's Markdown into HTML |
| `highlight.js` (CDN) | Syntax-highlights any code blocks in the answer |
| `DOMPurify` (CDN) | Sanitizes the parsed HTML before it's inserted into the DOM -- this is what makes rendering LLM-generated Markdown safe against XSS |

All three frontend libraries load from CDN, so there's no `npm install` /
bundler step. If you need an offline-only deployment, vendor those three
files locally and update the `<script>`/`<link>` tags in
`templates/index.html`.

## JSON API reference

Every endpoint returns JSON and gets the same security headers
(`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
`Referrer-Policy: no-referrer`).

### `POST /api/ask`

Request:
```json
{ "question": "How do I configure the chunk size?" }
```

Success response (`200`):
```json
{
  "answer": "You can configure it via CHUNK_SIZE in config.py [1]...",
  "sources": ["sample.md"],
  "cached": false
}
```

Error responses:
| Status | Cause |
|---|---|
| `400` | Missing or empty `"question"` field |
| `503` | No index built yet (`FileNotFoundError`) -- message is scrubbed of anything that looks like an API key |
| `500` | Unexpected error talking to the provider -- the real exception is logged server-side via `logger.exception`, but the client only ever sees a generic `"Something went wrong answering that question."` so provider errors (which sometimes embed request details) never leak to the browser |

curl example:
```bash
curl -s -X POST http://localhost:5050/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "How do I configure the chunk size?"}' | python -m json.tool
```

### `GET /api/sources`

Returns every distinct source file currently in the index:
```json
{ "sources": ["sample.md", "another-doc.md"] }
```
Returns `503` with the same shape as above if no index exists yet.

### `GET /api/stats`

Returns index + cache stats:
```json
{
  "total_chunks": 42,
  "total_sources": 3,
  "embed_model": "text-embedding-3-small",
  "chat_model": "gpt-4o",
  "cache": { "hits": 5, "misses": 12, "size": 12 }
}
```
Use this to confirm which models are actually active (handy after
switching providers in `.env`) and to watch the similarity cache's hit
rate.

### `GET /api/health`

```json
{ "status": "ok" }
```
A liveness check that never touches the index or any provider -- safe to
hit from an uptime monitor or load balancer health check.

## Security notes

- `app.run()` is called with `debug=False` explicitly. Never flip this to
  `True` in anything reachable outside your own machine -- Flask's debug
  mode exposes an interactive debugger that can execute arbitrary code.
- The provider API key is read once into `config.py` from `.env` and never
  put into a response body, header, or template context. `app._scrub()`
  additionally regex-strips anything that looks like an OpenAI/Anthropic
  style key (`sk-...`, `pk-...`) out of error messages as a defense-in-depth
  measure, in case a future error message ever embedded one.
- All exceptions from the provider call are caught generically in
  `/api/ask` and replaced with a fixed, generic message before reaching the
  client -- the only place provider error detail is visible is the server
  log (`logger.exception("ask failed")`).

## Running it for real (beyond your laptop)

`python app.py` uses Flask's built-in development server, which is fine
for local use but not meant for production traffic (no concurrency
tuning, no process management). For anything beyond local testing, run it
behind a real WSGI server, e.g.:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5050 app:app
```

Put a reverse proxy (nginx, Caddy, etc.) in front if you need TLS,
additional rate limiting, or to serve multiple apps on one host.

## Troubleshooting

**Page loads but every question returns a 503**
No index yet -- run `python ingest.py`, then refresh.

**Blank page / static files 404**
Make sure you're running `python app.py` from the project root (Flask
resolves `templates/` and `static/` relative to the app's location, but
double-check you haven't moved `app.py` without moving those folders too).

**Markdown renders as raw text, code isn't highlighted**
Check the browser console for blocked CDN requests (corporate proxies /
strict CSPs sometimes block `cdnjs.cloudflare.com`). If you need a fully
offline UI, vendor `marked.js`, `highlight.js`, and `DOMPurify` locally.

**"(answered from cache)" shows up for a question you never asked before**
The cache is similarity-based, not exact-match: any question whose
embedding is `>= CACHE_SIMILARITY_THRESHOLD` (default `0.95`) cosine-similar
to a previously asked question will reuse that answer. Lower the threshold
in `.env` (`CACHE_SIMILARITY_THRESHOLD`) if this feels too aggressive for
your docs.
