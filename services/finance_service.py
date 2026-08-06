import requests
import datetime
from typing import Dict, Any, List

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def search_ticker(query: str) -> str:
    """
    Search Yahoo Finance to resolve a company name (e.g. 'Apple') to its ticker symbol (e.g. 'AAPL').
    Returns the top ticker symbol found or the query itself if no ticker is found.
    """
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {'q': query, 'quotesCount': 1, 'newsCount': 0}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            quotes = data.get("quotes", [])
            if quotes:
                symbol = quotes[0].get("symbol")
                if symbol:
                    return symbol.upper()
    except Exception as e:
        print(f"Error in search_ticker: {e}")
    return query.upper()

def get_stock_quote(ticker: str) -> Dict[str, Any]:
    """
    Get stock quote data for a given ticker by calling the Yahoo Chart API.
    Bypasses yfinance crumb rate-limiting.
    """
    ticker_clean = ticker.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_clean}"
    try:
        r = requests.get(url, headers=HEADERS, params={'range': '1d'}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                prev_close = meta.get("chartPreviousClose")
                
                change = None
                pct_change = None
                if price is not None and prev_close is not None:
                    change = price - prev_close
                    pct_change = (change / prev_close) * 100
                    
                return {
                    "ticker": ticker_clean,
                    "name": meta.get("longName") or meta.get("shortName") or ticker_clean,
                    "price": price,
                    "currency": meta.get("currency", "USD"),
                    "change": round(change, 2) if change is not None else None,
                    "pct_change": round(pct_change, 2) if pct_change is not None else None,
                    "day_low": meta.get("regularMarketDayLow"),
                    "day_high": meta.get("regularMarketDayHigh"),
                    "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
                    "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
                    "market_cap": None,  # Not present in chart meta, fallback
                    "pe_ratio": None,
                    "dividend_yield": None,
                    "volume": meta.get("regularMarketVolume"),
                    "status": "success"
                }
        return {
            "ticker": ticker_clean,
            "status": "error",
            "message": f"Yahoo returned status code {r.status_code}"
        }
    except Exception as e:
        return {
            "ticker": ticker_clean,
            "status": "error",
            "message": str(e)
        }

def get_company_info(ticker: str) -> Dict[str, Any]:
    """
    Get detailed company profile and description via Yahoo Search API.
    """
    ticker_clean = ticker.strip().upper()
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {'q': ticker_clean, 'quotesCount': 5, 'newsCount': 0}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            quotes = data.get("quotes", [])
            for q in quotes:
                if q.get("symbol") == ticker_clean:
                    # Found match
                    sector = q.get("sector") or q.get("sectorDisp", "N/A")
                    industry = q.get("industry") or q.get("industryDisp", "N/A")
                    name = q.get("longname") or q.get("shortname") or ticker_clean
                    
                    return {
                        "ticker": ticker_clean,
                        "name": name,
                        "sector": sector,
                        "industry": industry,
                        "website": "N/A",
                        "description": f"{name} is a company in the {sector} sector operating within the {industry} industry, listed on the {q.get('exchange', 'N/A')} exchange.",
                        "employees": "N/A",
                        "ceo": "N/A",
                        "headquarters": "N/A",
                        "status": "success"
                    }
        # Fallback to chart meta
        quote = get_stock_quote(ticker_clean)
        if quote.get("status") == "success":
            return {
                "ticker": ticker_clean,
                "name": quote.get("name"),
                "sector": "N/A",
                "industry": "N/A",
                "website": "N/A",
                "description": f"{quote.get('name')} is a publicly traded company ticker '{ticker_clean}', priced in {quote.get('currency')}.",
                "employees": "N/A",
                "ceo": "N/A",
                "headquarters": "N/A",
                "status": "success"
            }
    except Exception as e:
        print(f"Error fetching company info for {ticker_clean}: {e}")
    return {
        "ticker": ticker_clean,
        "status": "error",
        "message": f"Failed to retrieve company profile for {ticker_clean}"
    }

def get_company_news(ticker: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get latest news related to a company.
    """
    ticker_clean = ticker.strip().upper()
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {'q': ticker_clean, 'quotesCount': 1, 'newsCount': limit}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            news = data.get("news", [])
            parsed_news = []
            for item in news[:limit]:
                # Format time
                parsed_news.append({
                    "title": item.get("title"),
                    "publisher": item.get("publisher"),
                    "link": item.get("link"),
                    "publish_time": "N/A", # News search response lacks detailed timestamps sometimes
                    "type": "STORY"
                })
            return parsed_news
    except Exception as e:
        print(f"Error fetching news for {ticker_clean}: {e}")
    return []

def get_earnings_calendar(ticker: str) -> Dict[str, Any]:
    """
    Mock upcoming earnings dates as a utility fallback.
    """
    ticker_clean = ticker.strip().upper()
    return {
        "ticker": ticker_clean,
        "earnings_dates": ["Scheduled quarterly. Check exchange website for specific dates."],
        "earnings_average": None,
        "earnings_low": None,
        "earnings_high": None,
        "revenue_average": None,
        "status": "success"
    }

def get_financials_summary(ticker: str) -> Dict[str, Any]:
    """
    Returns annual price performance summary derived from historical chart.
    """
    ticker_clean = ticker.strip().upper()
    chart = get_historical_prices(ticker_clean, period="1y")
    if chart.get("status") == "success" and chart.get("data"):
        data = chart["data"]
        # Take values spaced quarterly
        n = len(data)
        quarters = {}
        for idx in [0, n // 4, n // 2, (3 * n) // 4, n - 1]:
            if 0 <= idx < n:
                point = data[idx]
                quarters[point["date"]] = point["close"]
        return {
            "ticker": ticker_clean,
            "annual": {
                "Historical Close Price Trends": quarters
            },
            "status": "success"
        }
    return {
        "ticker": ticker_clean,
        "status": "error",
        "message": "Failed to compile financial summaries from historical charts."
    }

def compare_companies(ticker1: str, ticker2: str) -> Dict[str, Any]:
    """
    Compare two companies side-by-side using key financial metrics.
    """
    quote1 = get_stock_quote(ticker1)
    quote2 = get_stock_quote(ticker2)
    
    info1 = get_company_info(ticker1)
    info2 = get_company_info(ticker2)
    
    return {
        "company1": {
            "ticker": ticker1.upper(),
            "name": quote1.get("name"),
            "price": quote1.get("price"),
            "pct_change": quote1.get("pct_change"),
            "day_high": quote1.get("day_high"),
            "day_low": quote1.get("day_low"),
            "sector": info1.get("sector"),
            "industry": info1.get("industry")
        },
        "company2": {
            "ticker": ticker2.upper(),
            "name": quote2.get("name"),
            "price": quote2.get("price"),
            "pct_change": quote2.get("pct_change"),
            "day_high": quote2.get("day_high"),
            "day_low": quote2.get("day_low"),
            "sector": info2.get("sector"),
            "industry": info2.get("industry")
        },
        "status": "success"
    }

def get_historical_prices(ticker: str, period: str = "1mo") -> Dict[str, Any]:
    """
    Get historical close prices for plotting by calling the Yahoo Chart API.
    Bypasses yfinance.
    """
    ticker_clean = ticker.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_clean}"
    
    # Map periods to ranges/intervals
    # range: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    try:
        r = requests.get(url, headers=HEADERS, params={'range': period, 'interval': '1d'}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            result = data.get("chart", {}).get("result", [])
            if result:
                res = result[0]
                timestamps = res.get("timestamp", [])
                indicators = res.get("indicators", {}).get("quote", [{}])[0]
                
                opens = indicators.get("open", [])
                highs = indicators.get("high", [])
                lows = indicators.get("low", [])
                closes = indicators.get("close", [])
                volumes = indicators.get("volume", [])
                
                chart_points = []
                for i in range(len(timestamps)):
                    # Check for nulls which sometimes appear in Yahoo data
                    if closes[i] is None or opens[i] is None:
                        continue
                    dt = datetime.datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d')
                    chart_points.append({
                        "date": dt,
                        "open": round(opens[i], 2),
                        "high": round(highs[i], 2),
                        "low": round(lows[i], 2),
                        "close": round(closes[i], 2),
                        "volume": int(volumes[i]) if volumes[i] is not None else 0
                    })
                return {
                    "ticker": ticker_clean,
                    "period": period,
                    "data": chart_points,
                    "status": "success"
                }
        return {
            "ticker": ticker_clean,
            "status": "error",
            "message": f"Yahoo Chart API returned status code {r.status_code}"
        }
    except Exception as e:
        return {
            "ticker": ticker_clean,
            "status": "error",
            "message": str(e)
        }
