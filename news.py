import requests
from config import NEWS_API_KEY

def get_news(topic=None, count=5):
    try:
        if topic:
            url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize={count}&apiKey={NEWS_API_KEY}"
        else:
            url = f"https://newsapi.org/v2/top-headlines?country=us&pageSize={count}&apiKey={NEWS_API_KEY}"

        res = requests.get(url).json()
        articles = res.get("articles", [])
        if not articles:
            return "No news found, Sir."

        headlines = [f"{i+1}. {a['title']}" for i, a in enumerate(articles) if a.get('title')]
        return "Here are the top headlines, Sir:\n" + "\n".join(headlines)
    except Exception as e:
        return f"News service unavailable, Sir. Error: {e}"