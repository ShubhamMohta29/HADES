# SSRF Security Report

## Status: N/A

## Findings

HADES fetches URLs in four places, none of which use user-controlled URL values:

| Module | URL | User-controlled? |
|---|---|---|
| `services/weather.py` | `https://api.openweathermap.org/...?q={city}` | City name is a query param, not the URL itself |
| `services/news.py` | `https://newsapi.org/...?q={topic}` | Topic is a query param, not the URL |
| `services/stocks.py` | `https://api.coingecko.com/...?ids={coin_id}` | Coin ID is a query param, not the URL |
| `vision.py` | Groq API endpoint (hardcoded) | No user input in URL |
| `voice/tts.py` | HuggingFace model download (hardcoded) | No user input |

No feature accepts a user-provided URL to fetch. There is no link preview, image proxy, webhook URL tester, or import-from-URL feature.

Query parameters (city, topic, coin_id) are passed to `requests.get()` via the `params=` argument, which URL-encodes them safely. Even a malicious city name like `?evil=1` would be encoded as a query string value, not appended to the path. ✅

## Recommendations

N/A. If a web research agent (v2.0 roadmap) is added, implement SSRF protection: block private IP ranges, validate scheme (http/https only), resolve hostname and check IP before fetching.
