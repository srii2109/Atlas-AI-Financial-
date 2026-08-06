# 📊 Atlas AI: Conversational Financial Assistant & Dashboard

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com/)
[![Telegram](https://img.shields.io/badge/Telegram%20Bot-Active-blue.svg)](https://core.telegram.org/bots)
[![Gemini](https://img.shields.io/badge/Gemini%20AI-Generative%20Model-violet.svg)](https://deepmind.google/technologies/gemini/)
[![Docker](https://img.shields.io/badge/Docker-Compatible-blue.svg)](https://www.docker.com/)

**Atlas AI** is an advanced, conversational AI Financial Assistant designed specifically for finance professionals (investors, analysts, founders). It integrates **Telegram Bot interactions** with a **gorgeous Web Dashboard** to eliminate context switching, automate stock research, summarize financials, and deliver personalized briefings.

---

## 🚀 Key Features

*   🎯 **Conversational Onboarding**: Gathers user role, watchlists, and briefing schedules naturally through chat. Can be skipped at any moment.
*   🗣️ **Speech-to-text Conversational Queries**: Download and transcribe voice messages natively using Gemini, routing them through the tool-calling pipeline.
*   🔍 **Multi-Modal Document & Chart Audits**: Upload a chart, balance sheet, or report screenshot, and Atlas AI will provide instant visual analysis.
*   📈 **Live Financial Info (Direct APIs)**: Fetches stock quotes, 52-week stats, daily high/lows, index trends, and historical metrics directly from public REST endpoints, bypassing yfinance library rate limits.
*   ⏰ **Proactive Briefings & Price Alerts**: Automated scheduled jobs for personalized morning summaries and notifications when a watchlist ticker fluctuates by $\ge 5\%$.
*   🖥️ **Premium Web Dashboard**: A dark-themed glassmorphic terminal where users can:
    *   View live S&P 500, Nasdaq, and Dow Jones indicators.
    *   Explore interactive stock performance graphs using **Chart.js**.
    *   Monitor synced conversation logs from Telegram in real-time.
    *   **Sandbox Demo Mode**: Test the bot interface on the webpage immediately using Telegram ID `99999` with pre-filled mock histories and stock watchlists.

---

## 🛠️ Technology Stack

1.  **Backend Framework**: Python (FastAPI + Uvicorn) for the Web dashboard APIs; `python-telegram-bot` for async webhook/long-polling handler.
2.  **Database**: SQLite (`peewee` ORM) storing profiles, preferences, watchlists, and conversation memories.
3.  **AI Engine**: Gemini API (`google-generativeai`) configured with functional tool declarations to call financial APIs on-demand.
4.  **Scheduler**: `apscheduler` managing background briefings and watchlist alerts.
5.  **Frontend styling**: Vanilla HTML5/CSS3 utilizing sleek dark mode gradients, glassmorphism, responsive visual rows, and interactive JavaScript.

---

## 📂 Project Structure

```
e:/Hackathon/
├── .env.example            # Template for bot token and API keys
├── requirements.txt        # Python package dependencies
├── Dockerfile              # Docker configuration for cloud deployment
├── bot.py                  # Main entry point for the Telegram bot pollers
├── server.py               # Main entry point for the FastAPI web server
├── config.py               # Settings loader and validator
├── database/
│   ├── __init__.py
│   ├── connection.py       # SQLite connection instantiations
│   └── models.py           # DB tables for Users, Watchlist, History, etc.
├── services/
│   ├── __init__.py
│   ├── ai_service.py       # Gemini Chat session manager, multi-modal wrappers
│   ├── finance_service.py  # Yahoo Finance REST quote/chart/search scrapers
│   └── scheduler_service.py# APScheduler jobs for briefings & alerts
├── handlers/
│   ├── __init__.py
│   ├── onboarding.py       # State machine for conversational onboarding
│   └── message_handler.py  # Router for text, voice notes, and images
├── templates/
│   ├── landing.html        # Interactive landing page with simulated terminal
│   └── dashboard.html      # Glassmorphic user dashboard
└── static/
    └── css/
        └── style.css       # Premium styles, animations, layouts
```

---

## ⚙️ Installation & Setup

### Prerequisites
*   Python 3.11+ (Fully patched and verified compatible with Python 3.14)
*   Telegram Bot Token (via `@BotFather`)
*   Gemini API Key (via [Google AI Studio](https://aistudio.google.com/))

### 1. Clone the repository
```bash
git clone <repository_url>
cd e:/Hackathon
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your tokens:
```bash
cp .env.example .env
```
Inside `.env`:
```ini
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Web Server
Launch the FastAPI server which compiles the dashboard and serves the web experience:
```bash
python server.py
```
Visit the landing page at [http://localhost:8000](http://localhost:8000) and the dashboard at [http://localhost:8000/dashboard](http://localhost:8000/dashboard).

### 5. Start the Telegram Bot
In a separate terminal, start the bot listener:
```bash
python bot.py
```
Open Telegram, search for your bot, and send `/start` to begin the onboarding!

---

## 🐳 Docker Deployment

The project is fully containerized. You can build and run it locally or deploy it directly to platforms like **Railway**, **Render**, or **Heroku**:

```bash
# Build the container
docker build -t atlas-ai-finance .

# Run the container
docker run -p 8000:8000 --env-file .env atlas-ai-finance
```

---

## 🧪 Verification & Testing
To ensure the SQLite database, Yahoo direct endpoints, and Gemini configurations are working correctly, run the verification script:
```bash
python C:\Users\Srikari\.gemini\antigravity\brain\918a349d-2596-4aa7-99b6-3bc05635eb72\scratch\verify_services.py
```
All outputs should show `SUCCESS` and `ALL BASIC VERIFICATIONS PASSED!`.
