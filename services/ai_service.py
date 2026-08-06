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
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
import config
from services.finance_service import (
    get_stock_quote,
    get_company_info,
    get_company_news,
    get_earnings_calendar,
    get_financials_summary,
    compare_companies,
    get_historical_prices,
    search_ticker
)
from database.models import ConversationHistory, User
import datetime

# Persona and instructions for the Financial Assistant
SYSTEM_INSTRUCTION = """
You are Atlas AI, a highly experienced and intuitive financial analyst who also serves as a general-purpose AI assistant. You must be able to answer ANY question the user asks (like general knowledge, coding, writing, math, or explanation of concepts), just like ChatGPT, while remaining highly capable in financial markets.

Follow these guidelines for all responses:
1. Scope: You are a general-purpose AI. If a user asks general queries (e.g. "write a python script to check prime numbers", "explain quantum physics", or "draft an email"), answer them fully and directly.
2. Tone: Conversational, professional, welcoming, and intelligent. Never sound like a generic command-driven bot.
3. Formats: Speak in natural language. Avoid command-driven menus or slash lists.
4. Clarity: Focus on high-fidelity, concise answers. Use bullet points and small markdown tables for comparisons and structural data.
5. Ambiguity in Finance: If a user asks a finance-specific request that is ambiguous (e.g. "Tell me about Nvidia"), ask a natural follow-up question to clarify whether they want stock quotes, company profiles, news, or history.
6. Accuracy: You have access to real-time stock data and financial metrics tools. Use them to answer user questions. If a tool fails, be transparent. Never hallucinate numbers.
7. Context: You remember previous messages in the conversation to deliver continuous support.
"""

def init_ai():
    if config.GEMINI_API_KEY:
        genai.configure(api_key=config.GEMINI_API_KEY)
        print("Gemini API configured successfully.")
    else:
        print("Warning: GEMINI_API_KEY is not set. Running in Mock AI mode.")

# Instantiate list of tool functions
financial_tools = [
    get_stock_quote,
    get_company_info,
    get_company_news,
    get_earnings_calendar,
    get_financials_summary,
    compare_companies,
    get_historical_prices,
    search_ticker
]

def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """
    Transcribe speech to text using Gemini's native audio capability.
    """
    if not config.GEMINI_API_KEY:
        return "Audio transcription is unavailable (no API Key)."
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        audio_part = {
            "mime_type": mime_type,
            "data": audio_bytes
        }
        response = model.generate_content([
            audio_part,
            "Transcribe the spoken words in this audio file. Output only the transcription text, nothing else. If there is no speech, return an empty string."
        ])
        return response.text.strip()
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return f"[Audio transcription error: {e}]"

def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg", user_prompt: str = "Analyze this image.") -> str:
    """
    Analyze financial documents or stock charts uploaded by the user.
    """
    if not config.GEMINI_API_KEY:
        return "Image analysis is unavailable in mock mode."
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }
        prompt = f"The user uploaded this image. Please analyze it. Prompt: {user_prompt}"
        response = model.generate_content([image_part, prompt])
        return response.text
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return f"Error analyzing image: {e}"

def generate_chat_response(user_id: int, user_message: str) -> str:
    """
    Process conversational messages, keeping context and leveraging function tools.
    """
    if not config.GEMINI_API_KEY:
        # Mock responses for local testing without keys
        user_message_lower = user_message.lower()
        if "aapl" in user_message_lower or "apple" in user_message_lower:
            return "Mock Stock Update:\nApple Inc. (AAPL) is trading at $185.40 (+1.25%)."
        if "compare" in user_message_lower:
            return "Mock Comparison:\n| Metric | AAPL | MSFT |\n|---|---|---|\n| Price | $185.40 | $415.50 |\n| Cap | $2.85T | $3.1T |"
        return f"Hello, I am Atlas AI (Mock Mode). You said: '{user_message}'. Please configure GEMINI_API_KEY to enable full conversational intelligence and real-time financial tracking."

    try:
        # Fetch conversation history from SQLite
        db_history = ConversationHistory.select().where(ConversationHistory.user_id == user_id).order_by(ConversationHistory.timestamp.desc()).limit(15)
        # Convert to chronological order
        db_history = list(reversed(db_history))
        
        # Format history for Gemini
        gemini_history = []
        for h in db_history:
            role = "user" if h.sender == "user" else "model"
            gemini_history.append({
                "role": role,
                "parts": [h.content]
            })
            
        # Instantiate generative model with tools
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=financial_tools,
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Start a chat session with historical messages
        chat = model.start_chat(history=gemini_history, enable_automatic_function_calling=True)
        
        # Send user's new message
        response = chat.send_message(user_message)
        
        return response.text
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return f"I ran into an issue while analyzing that request: {e}"

# Run initialization
init_ai()
