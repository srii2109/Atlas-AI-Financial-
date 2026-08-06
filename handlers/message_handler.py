import datetime
import telegram
from telegram import Update
from telegram.ext import ContextTypes
from database.models import User, ConversationHistory
from handlers.onboarding import process_onboarding
from services.ai_service import generate_chat_response, transcribe_audio, analyze_image

async def safe_reply(update: Update, text: str):
    try:
        await update.message.reply_text(text, parse_mode="Markdown")
    except telegram.error.BadRequest:
        # Fallback to raw text if Markdown parsing fails
        await update.message.reply_text(text, parse_mode=None)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Primary message handler that routes incoming text, voice, and images.
    """
    if not update.message:
        return
        
    tg_user = update.effective_user
    user_id = tg_user.id
    username = tg_user.username
    first_name = tg_user.first_name
    
    # Get or create User in database
    user, created = User.get_or_create(
        telegram_id=user_id,
        defaults={
            "username": username,
            "first_name": first_name,
            "onboarding_status": "not_started",
            "onboarding_step": 0
        }
    )
    
    # Check if this is a voice note
    if update.message.voice:
        # Download voice note
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        voice_bytes = await voice_file.download_as_bytearray()
        
        # Notify user that we are listening
        listening_msg = await update.message.reply_text("🔊 *Listening to voice note...*", parse_mode="Markdown")
        
        # Transcribe speech
        transcribed_text = transcribe_audio(bytes(voice_bytes), mime_type="audio/ogg")
        await listening_msg.delete()
        
        if not transcribed_text.strip():
            await update.message.reply_text("I couldn't hear any speech in that voice note. Could you try speaking again or typing your message?")
            return
            
        # Replying text back to user
        await safe_reply(update, f"🗣️ *You asked:* _{transcribed_text}_")
        
        # Send transcribed text through standard pipeline
        await process_text_input(user, transcribed_text, update, media_type="voice")
        
    # Check if this is an image
    elif update.message.photo:
        photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
        image_bytes = await photo_file.download_as_bytearray()
        
        caption = update.message.caption or "Analyze this financial image."
        
        analyzing_msg = await update.message.reply_text("🔍 *Analyzing chart/document...*", parse_mode="Markdown")
        
        # Save user interaction in history
        ConversationHistory.create(
            user=user,
            sender="user",
            content=f"[Image Uploaded] Caption: {caption}",
            media_type="image"
        )
        
        # Run visual analysis
        ai_response = analyze_image(bytes(image_bytes), mime_type="image/jpeg", user_prompt=caption)
        await analyzing_msg.delete()
        
        # Save AI reply
        ConversationHistory.create(
            user=user,
            sender="assistant",
            content=ai_response,
            media_type="text"
        )
        
        await safe_reply(update, ai_response)
        
    # Standard text messages
    elif update.message.text:
        text = update.message.text
        
        # Check if user is in onboarding phase
        if user.onboarding_status != "completed":
            # Save message
            ConversationHistory.create(
                user=user,
                sender="user",
                content=text,
                media_type="text"
            )
            
            # Onboarding processing
            reply = process_onboarding(user, text)
            
            # Save bot message
            ConversationHistory.create(
                user=user,
                sender="assistant",
                content=reply,
                media_type="text"
            )
            
            await safe_reply(update, reply)
        else:
            # Process normal chat message
            await process_text_input(user, text, update)

async def process_text_input(user: User, text: str, update: Update, media_type: str = "text"):
    """
    Helper to process text input (or transcribed voice) through Gemini's chat agent.
    """
    # Save user message to database
    ConversationHistory.create(
        user=user,
        sender="user",
        content=text,
        media_type=media_type
    )
    
    # Process through Gemini AI agent (automatic tool execution is handled inside)
    reply_text = generate_chat_response(user.telegram_id, text)
    
    # Save AI response to database
    ConversationHistory.create(
        user=user,
        sender="assistant",
        content=reply_text,
        media_type="text"
    )
    
    # Respond to user
    await safe_reply(update, reply_text)
