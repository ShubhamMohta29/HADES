import requests
from config import NEWS_API_KEY


def get_news(topic: str | None = None, count: int = 5) -> str:
    if not NEWS_API_KEY:
        return "News service offline — no API key configured, Sir."
    try:
        if topic:
            url = "https://newsapi.org/v2/everything"
            params = {"q": topic, "sortBy": "publishedAt",
                      "pageSize": count, "apiKey": NEWS_API_KEY}
        else:
            url = "https://newsapi.org/v2/top-headlines"
            params = {"country": "us", "pageSize": count, "apiKey": NEWS_API_KEY}

        res = requests.get(url, params=params, timeout=8).json()
        articles = res.get("articles", [])
        if not articles:
            return "No news found, Sir."

        headlines = [f"{i+1}. {a['title']}"
                     for i, a in enumerate(articles) if a.get("title")]
        return "Here are the top headlines, Sir:\n" + "\n".join(headlines)
    except requests.Timeout:
        return "The news service is taking too long to respond, Sir."
    except Exception as e:
        return f"News service unavailable, Sir. Error: {e}"
