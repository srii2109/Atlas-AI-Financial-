import datetime
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.models import User, UserPreference, Watchlist, ConversationHistory
from services.finance_service import get_stock_quote, get_company_news
import google.generativeai as genai
import config

async def generate_briefing_content(user: User) -> str:
    """
    Generate personalized briefing content for a user based on their watchlist and interests.
    """
    # Fetch watchlist
    watchlist_items = Watchlist.select().where(Watchlist.user == user)
    tickers = [item.ticker for item in watchlist_items]
    
    # Fetch indices
    indices = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones"}
    index_summaries = []
    for ticker, name in indices.items():
        quote = get_stock_quote(ticker)
        if quote.get("status") == "success" and quote.get("price"):
            change_str = f"{quote['price']} ({quote['pct_change']}%"
            if quote['change'] >= 0:
                change_str = f"📈 {quote['price']} (+{quote['pct_change']}%)"
            else:
                change_str = f"📉 {quote['price']} ({quote['pct_change']}%)"
            index_summaries.append(f"{name}: {change_str}")
            
    # Fetch watchlist stock updates
    stock_summaries = []
    for ticker in tickers:
        quote = get_stock_quote(ticker)
        if quote.get("status") == "success" and quote.get("price"):
            direction = "📈" if quote['change'] >= 0 else "📉"
            sign = "+" if quote['change'] >= 0 else ""
            stock_summaries.append(
                f"{direction} **{quote['ticker']}** ({quote['name']}): "
                f"${quote['price']} ({sign}{quote['pct_change']}%)"
            )
            
    # Compile briefing prompt for Gemini
    indices_text = "\n".join(index_summaries)
    watchlist_text = "\n".join(stock_summaries) if stock_summaries else "No stocks in watchlist."
    interests = user.preferences[0].interests if user.preferences else "Finance, Markets"
    
    prompt = f"""
    Create a highly professional and concise Morning Market Briefing for a finance professional who is a {user.role}.
    Here is the market data:
    
    Major Market Indices:
    {indices_text}
    
    Their Watchlist Updates:
    {watchlist_text}
    
    Their general interests: {interests}
    
    Provide:
    1. A quick 2-3 sentence executive summary of market sentiment.
    2. Key highlights of their watchlist stocks.
    3. 1-2 bullet points explaining why today's movements matter.
    
    Keep the tone conversational, sharp, and brief. Format with clean markdown bolding. No slash commands, no emojis overload.
    """
    
    try:
        if config.GEMINI_API_KEY:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            briefing = response.text
        else:
            briefing = f"**Morning Briefing (Mock Mode)**\n\n**Indices:**\n{indices_text}\n\n**Watchlist:**\n{watchlist_text}\n\nMarket sentiment appears steady. Keep an eye on earnings scheduled this week."
            
        # Log to chat history as assistant sender
        ConversationHistory.create(
            user=user,
            sender="assistant",
            content=briefing,
            media_type="text"
        )
        return briefing
    except Exception as e:
        print(f"Error generating briefing content: {e}")
        return f"Could not generate briefing due to error: {e}"

async def send_daily_briefings(bot_app):
    """
    Cron job triggered hourly or minutely to find users whose briefing time is now and send briefings.
    """
    now = datetime.datetime.now()
    time_str = now.strftime("%H:%M")
    print(f"Checking briefings for current time: {time_str}")
    
    # Query users whose preferred briefing time matches current hour and minute
    preferences = UserPreference.select().where(
        (UserPreference.briefing_time == time_str) & 
        (UserPreference.notification_enabled == True)
    )
    
    for pref in preferences:
        user = pref.user
        print(f"Sending daily briefing to user {user.telegram_id}")
        briefing = await generate_briefing_content(user)
        try:
            # send via telegram bot
            try:
                await bot_app.bot.send_message(
                    chat_id=user.telegram_id,
                    text=briefing,
                    parse_mode="Markdown"
                )
            except Exception as pe:
                await bot_app.bot.send_message(
                    chat_id=user.telegram_id,
                    text=briefing,
                    parse_mode=None
                )
        except Exception as e:
            print(f"Failed to send briefing to {user.telegram_id}: {e}")

async def check_watchlist_alerts(bot_app):
    """
    Job that checks watchlist price fluctuations and sends alert if move exceeds 5%.
    """
    print("Checking watchlist alerts...")
    watchlist_items = Watchlist.select()
    
    # Store ticker quotes to avoid multiple fetches for the same ticker
    quotes = {}
    
    for item in watchlist_items:
        ticker = item.ticker
        if ticker not in quotes:
            quotes[ticker] = get_stock_quote(ticker)
            
        quote = quotes[ticker]
        if quote.get("status") == "success" and quote.get("price"):
            pct_change = quote.get("pct_change", 0.0)
            
            # Check for standard 5% fluctuation alert
            if abs(pct_change) >= 5.0:
                direction = "surged" if pct_change > 0 else "dropped"
                alert_msg = f"⚠️ **Watchlist Alert**: **{quote['ticker']}** ({quote['name']}) has {direction} by **{quote['pct_change']}%** today, currently trading at **${quote['price']}**."
                
                try:
                    try:
                        await bot_app.bot.send_message(
                            chat_id=item.user.telegram_id,
                            text=alert_msg,
                            parse_mode="Markdown"
                        )
                    except Exception as pe:
                        await bot_app.bot.send_message(
                            chat_id=item.user.telegram_id,
                            text=alert_msg,
                            parse_mode=None
                        )
                except Exception as e:
                    print(f"Failed to send alert to {item.user.telegram_id}: {e}")

def start_scheduler(bot_app):
    scheduler = AsyncIOScheduler()
    # Check briefings every minute
    scheduler.add_job(send_daily_briefings, 'cron', minute='*', args=[bot_app])
    # Check watchlist price moves every 15 minutes
    scheduler.add_job(check_watchlist_alerts, 'cron', minute='*/15', args=[bot_app])
    scheduler.start()
    print("Scheduler started successfully.")
