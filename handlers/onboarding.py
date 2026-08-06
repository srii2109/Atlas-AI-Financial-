from database.models import User, UserPreference, Watchlist, ConversationHistory
from services.finance_service import search_ticker
import re
import datetime

ONBOARDING_STEPS = {
    0: "Welcome to Atlas AI, your personal financial analyst. I'm here to help you conduct research, monitor markets, and simplify your daily financial workflow.\n\nTo tailor my insights for you, what best describes your role? (e.g., Investor, Analyst, Founder, Student, or Finance Professional)",
    1: "Got it! Which specific companies, sectors, or markets do you actively follow? (List names or tickers, e.g., Tesla, AI, or semiconductor)",
    2: "Got it. When would you like to receive your daily morning briefing? Please reply with a time (e.g., 08:30 in HH:MM format), or type 'skip' to skip.",
    3: "Awesome! Your profile is set up. You can ask me for stock quotes, financial statements, comparisons, news summaries, or even upload reports and charts. You can also send voice messages.\n\nHow can I help you today?"
}

def extract_tickers(text: str) -> list:
    """
    Tries to extract stock tickers from text using regex and word splits.
    """
    # Find all words that look like tickers (all caps, 1-5 letters)
    candidates = re.findall(r'\b[A-Za-z]{1,5}\b', text)
    tickers = []
    for c in candidates:
        c_upper = c.upper()
        # Filter out common skip words
        if c_upper not in ["I", "AI", "AM", "TO", "A", "AND", "OR", "BUT", "THE", "IN", "ON", "FOR", "OF", "AT", "BY", "SKIP"]:
            tickers.append(c_upper)
    return list(set(tickers))

def process_onboarding(user: User, text: str) -> str:
    """
    State machine for conversational onboarding.
    Returns the message to send back to the user.
    """
    text_stripped = text.strip().lower()
    
    # Check if user wants to skip onboarding entirely or asks a financial question
    is_financial_query = any(keyword in text_stripped for keyword in ["price", "stock", "quote", "vs", "compare", "financial", "chart", "news", "revenue"])
    if text_stripped in ["skip all", "cancel onboarding", "stop onboarding"] or (user.onboarding_step == 0 and is_financial_query):
        user.onboarding_status = "completed"
        user.save()
        return "Understood. I've skipped onboarding. How can I help you with your financial research today?"
        
    step = user.onboarding_step
    
    if step == 0:
        # First message (user saying /start or something similar)
        user.onboarding_status = "in_progress"
        user.onboarding_step = 1
        user.save()
        return ONBOARDING_STEPS[0]
        
    elif step == 1:
        # User replied with their role
        role = text.strip()
        user.role = role
        user.onboarding_step = 2
        user.save()
        return f"Nice to meet you as a {role}! " + ONBOARDING_STEPS[1]
        
    elif step == 2:
        # User replied with companies, sectors, or markets they follow
        interests = text.strip()
        
        # Save interests to preference
        pref, created = UserPreference.get_or_create(user=user)
        pref.interests = interests
        pref.save()
        
        # Try to extract stocks/tickers and add to watchlist
        potential_tickers = extract_tickers(interests)
        added_tickers = []
        for ticker in potential_tickers:
            resolved = search_ticker(ticker)
            try:
                Watchlist.get_or_create(user=user, ticker=resolved)
                added_tickers.append(resolved)
            except Exception as e:
                print(f"Error adding {resolved} to watchlist: {e}")
                
        user.onboarding_step = 3
        user.save()
        
        watchlist_msg = ""
        if added_tickers:
            watchlist_msg = f"I've added {', '.join(added_tickers)} to your watchlist. "
            
        return f"Thanks! {watchlist_msg}" + ONBOARDING_STEPS[2]
        
    elif step == 3:
        # User replied with briefing time
        pref, created = UserPreference.get_or_create(user=user)
        
        if text_stripped != "skip":
            # Verify time format HH:MM
            time_match = re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', text_stripped)
            if time_match:
                pref.briefing_time = text_stripped
                pref.save()
            else:
                return "That doesn't look like a valid 24-hour time. Please write it in HH:MM format (e.g. 08:30) or type 'skip'."
                
        # Finish onboarding
        user.onboarding_status = "completed"
        user.onboarding_step = 4
        user.save()
        return ONBOARDING_STEPS[3]
        
    else:
        # Fallback
        user.onboarding_status = "completed"
        user.save()
        return "How can I help you today?"
