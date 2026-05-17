import requests


def get_stock(symbol: str) -> str:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}"
        params = {"interval": "1d", "range": "1d"}
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, params=params, headers=headers, timeout=8).json()
        meta = res["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev  = meta["previousClose"]
        change = round(price - prev, 2)
        pct = round((change / prev) * 100, 2)
        direction = "up" if change >= 0 else "down"
        return (f"{symbol.upper()} is trading at ${price:.2f}, "
                f"{direction} {abs(change):.2f} ({abs(pct):.2f}%) today, Sir.")
    except requests.Timeout:
        return "Yahoo Finance is taking too long to respond, Sir."
    except Exception:
        return f"Could not retrieve stock data for {symbol}, Sir."


def get_crypto(symbol: str) -> str:
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": symbol.lower(), "vs_currencies": "usd",
                  "include_24hr_change": "true"}
        res = requests.get(url, params=params, timeout=8).json()
        if symbol.lower() not in res:
            return f"Could not find {symbol}, Sir."
        data = res[symbol.lower()]
        price = data["usd"]
        change = round(data.get("usd_24h_change", 0), 2)
        direction = "up" if change >= 0 else "down"
        return (f"{symbol.upper()} is at ${price:,.2f}, "
                f"{direction} {abs(change):.2f}% in the last 24 hours, Sir.")
    except requests.Timeout:
        return "CoinGecko is taking too long to respond, Sir."
    except Exception:
        return "Crypto service unavailable, Sir."
