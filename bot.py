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
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN, validate_config
from database.models import init_db, User, ConversationHistory
from handlers.onboarding import ONBOARDING_STEPS
from handlers.message_handler import handle_message
from services.scheduler_service import start_scheduler

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command. Initializes or resets user onboarding.
    """
    tg_user = update.effective_user
    user_id = tg_user.id
    
    # Reset/Create User onboarding
    user, created = User.get_or_create(
        telegram_id=user_id,
        defaults={
            "username": tg_user.username,
            "first_name": tg_user.first_name
        }
    )
    user.onboarding_status = "not_started"
    user.onboarding_step = 1
    user.save()
    
    # Save command to history
    ConversationHistory.create(
        user=user,
        sender="user",
        content="/start",
        media_type="text"
    )
    
    welcome_text = ONBOARDING_STEPS[0]
    
    ConversationHistory.create(
        user=user,
        sender="assistant",
        content=welcome_text,
        media_type="text"
    )
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

def main():
    print("Starting Atlas AI Financial Assistant Bot...")
    
    # 1. Initialize SQLite Database Tables
    init_db()
    
    # 2. Validate environment configurations
    if not validate_config():
        print("Error: Configuration validation failed. Ensure your .env file is set up.")
        sys.exit(1)
        
    # 3. Build the Telegram bot application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 4. Add command and message handlers
    application.add_handler(CommandHandler("start", start_cmd))
    
    # Route all text, voice, and photo attachments
    application.add_handler(MessageHandler(
        filters.TEXT | filters.VOICE | filters.PHOTO, 
        handle_message
    ))
    
    # 5. Start background jobs scheduler (daily briefings, alerts)
    start_scheduler(application)
    
    # 6. Start the long-polling loop
    print("Atlas AI Bot is polling for updates...")
    application.run_polling()

if __name__ == "__main__":
    main()
