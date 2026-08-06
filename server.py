# Python 3.14 compatibility monkeypatch for protobuf upb c-extension
import builtins
import importlib

original_import = builtins.__import__
def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name and "google._upb" in name:
        raise ImportError("google._upb is disabled for Python 3.14 compatibility")
    if fromlist:
        for f in fromlist:
            if f == "_upb":
                raise ImportError("google._upb is disabled for Python 3.14 compatibility")
    return original_import(name, globals, locals, fromlist, level)
builtins.__import__ = custom_import

original_import_module = importlib.import_module
def custom_import_module(name, package=None):
    if name and "google._upb" in name:
        raise ImportError("google._upb is disabled for Python 3.14 compatibility")
    return original_import_module(name, package)
importlib.import_module = custom_import_module

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jinja2 import Template
import datetime

# Import database, configuration, and services
from config import PORT
from database.models import init_db, User, UserPreference, Watchlist, ConversationHistory
from services.finance_service import get_stock_quote, get_historical_prices, search_ticker
from services.ai_service import generate_chat_response

app = FastAPI(title="Atlas AI Financial Assistant API")

# Ensure static files directory exists and is mounted
os.makedirs("static/css", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatPayload(BaseModel):
    user_id: int
    message: str

class WatchlistPayload(BaseModel):
    user_id: int
    ticker: str

def create_sandbox_user():
    """
    Pre-populates a sandbox user (ID: 99999) with watchlists and conversations
    so the web dashboard works out-of-the-box for demo judges.
    """
    init_db()
    
    # 1. Create user
    user, created = User.get_or_create(
        telegram_id=99999,
        defaults={
            "username": "sandbox_analyst",
            "first_name": "Premium Analyst",
            "role": "Founder & Investor",
            "onboarding_status": "completed",
            "onboarding_step": 4
        }
    )
    
    # 2. Preferences
    pref, pref_created = UserPreference.get_or_create(
        user=user,
        defaults={
            "briefing_time": "08:30",
            "interests": "AI technology, semiconductors, electric vehicles",
            "briefing_scope": "market_news,watchlist_updates"
        }
    )
    
    # 3. Watchlist
    tickers = ["AAPL", "TSLA", "MSFT", "NVDA"]
    for t in tickers:
        Watchlist.get_or_create(user=user, ticker=t)
        
    # 4. Create sample conversation history if empty
    if ConversationHistory.select().where(ConversationHistory.user == user).count() == 0:
        samples = [
            ("user", "What is Nvidia's stock price today?"),
            ("assistant", "NVIDIA Corporation (NVDA) is trading at $875.12, up 3.45% today. Market Cap stands at $2.19T with a P/E ratio of 74.8."),
            ("user", "Compare Tesla and Microsoft"),
            ("assistant", "Here is a comparison between Tesla (TSLA) and Microsoft (MSFT):\n\n| Metric | TSLA | MSFT |\n|---|---|---|\n| Current Price | $175.40 | $415.50 |\n| Day Change | -1.8% | +0.75% |\n| Market Cap | $550B | $3.1T |\n| P/E Ratio | 45.2 | 36.8 |\n| Primary Sector | Consumer Cyclical | Technology |"),
            ("user", "What are the key market indices doing?")
        ]
        
        # We also need an assistant response for the last user prompt
        samples.append(("assistant", "Indices summary:\n📈 S&P 500: 5,420.30 (+0.45%)\n📈 NASDAQ: 16,845.20 (+0.80%)\n📉 Dow Jones: 38,980.50 (-0.12%)"))
        
        base_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        for i, (sender, content) in enumerate(samples):
            ConversationHistory.create(
                user=user,
                sender=sender,
                content=content,
                media_type="text",
                timestamp=base_time + datetime.timedelta(minutes=5 * i)
            )
            
    print("Sandbox user database entries verified.")

@app.on_event("startup")
def on_startup():
    create_sandbox_user()

# PAGE ROUTES
@app.get("/", response_class=HTMLResponse)
def get_landing():
    with open("templates/landing.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    with open("templates/dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# API ENDPOINTS
@app.post("/api/chat")
def api_chat(payload: ChatPayload):
    """
    Simulated chat endpoint used by the landing page terminal widget.
    """
    user, created = User.get_or_create(
        telegram_id=payload.user_id,
        defaults={
            "username": "web_guest",
            "first_name": "Web Guest",
            "role": "General User",
            "onboarding_status": "completed",
            "onboarding_step": 4
        }
    )
    
    # Save user prompt
    ConversationHistory.create(
        user=user,
        sender="user",
        content=payload.message,
        media_type="text"
    )
    
    # Generate bot response (with tool capability)
    response = generate_chat_response(payload.user_id, payload.message)
    
    # Save bot response
    ConversationHistory.create(
        user=user,
        sender="assistant",
        content=response,
        media_type="text"
    )
    
    return {"response": response}

@app.get("/api/user/{telegram_id}")
def api_get_user(telegram_id: int):
    """
    Fetches user profile, interests, watchlist ticker quotes, and conversation logs.
    """
    try:
        user = User.get_or_none(User.telegram_id == telegram_id)
        if not user:
            # If not found, create a sandbox or guest user so the screen isn't broken
            user = User.create(
                telegram_id=telegram_id,
                username=f"user_{telegram_id}",
                first_name=f"User {telegram_id}",
                role="Investor",
                onboarding_status="completed"
            )
            UserPreference.create(user=user, interests="Finance, Stocks")
            Watchlist.create(user=user, ticker="AAPL")
            Watchlist.create(user=user, ticker="TSLA")
            
        pref = UserPreference.get_or_none(UserPreference.user == user)
        briefing_time = pref.briefing_time if pref else "08:30"
        interests = pref.interests if pref else "Finance, Stocks"
        
        # Load watchlist tickers with their live quotes
        watchlist_items = Watchlist.select().where(Watchlist.user == user)
        watchlist_quotes = []
        for item in watchlist_items:
            quote = get_stock_quote(item.ticker)
            if quote.get("status") == "success":
                watchlist_quotes.append({
                    "ticker": item.ticker,
                    "name": quote.get("name"),
                    "price": quote.get("price"),
                    "pct_change": quote.get("pct_change")
                })
            else:
                watchlist_quotes.append({
                    "ticker": item.ticker,
                    "name": item.ticker,
                    "price": None,
                    "pct_change": None
                })
                
        # Load conversation history
        history_items = ConversationHistory.select().where(ConversationHistory.user == user).order_by(ConversationHistory.timestamp.desc()).limit(20)
        history_list = []
        for h in history_items:
            history_list.append({
                "sender": h.sender,
                "content": h.content,
                "timestamp": h.timestamp.isoformat()
            })
            
        return {
            "status": "success",
            "user": {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "role": user.role,
                "briefing_time": briefing_time,
                "interests": interests
            },
            "watchlist": watchlist_quotes,
            "history": history_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/add")
def api_add_watchlist(payload: WatchlistPayload):
    """
    Adds a ticker symbol to a user's watchlist.
    """
    try:
        user = User.get_or_none(User.telegram_id == payload.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        ticker = payload.ticker.strip().upper()
        # Resolve ticker using search tool if needed
        resolved_ticker = search_ticker(ticker)
        
        # Fetch quote to verify if valid ticker
        quote = get_stock_quote(resolved_ticker)
        if quote.get("status") == "error" or not quote.get("price"):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": f"Ticker symbol '{ticker}' is invalid or has no market data."}
            )
            
        Watchlist.get_or_create(user=user, ticker=resolved_ticker)
        return {"status": "success", "ticker": resolved_ticker}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/remove")
def api_remove_watchlist(payload: WatchlistPayload):
    """
    Removes a ticker symbol from user's watchlist.
    """
    try:
        user = User.get_or_none(User.telegram_id == payload.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        ticker = payload.ticker.strip().upper()
        q = Watchlist.delete().where((Watchlist.user == user) & (Watchlist.ticker == ticker))
        q.execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quote/{ticker}")
def api_get_quote(ticker: str):
    """
    Get live quote details for a specific stock ticker.
    """
    quote = get_stock_quote(ticker)
    return quote

@app.get("/api/chart/{ticker}")
def api_get_chart(ticker: str, period: str = "1mo"):
    """
    Get historical price chart data for plotting.
    """
    chart_data = get_historical_prices(ticker, period)
    return chart_data

if __name__ == "__main__":
    print(f"Starting FastAPI web server on http://localhost:{PORT}...")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
