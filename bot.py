import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI Client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! Send or forward me any voice message, and I will transcribe it to text for you!"
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Downloads the voice note and transcribes it using OpenAI Whisper."""
    # Let the user know the bot is working
    status_message = await update.message.reply_text("Processing your voice note... 🎧")
    
    try:
        # 1. Get the voice file metadata from Telegram
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        
        # 2. Define local file paths for downloading
        local_ogg_path = f"{update.message.voice.file_id}.ogg"
        
        # 3. Download the file from Telegram's servers
        await voice_file.download_to_drive(local_ogg_path)
        
        # 4. Open and send the file to OpenAI Whisper API
        with open(local_ogg_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        # 5. Clean up the downloaded local file
        if os.path.exists(local_ogg_path):
            os.remove(local_ogg_path)
            
        # 6. Send the transcribed text back to the user
        await status_message.edit_text(f"**Transcription:**\n\n{transcript.text}")

    except Exception as e:
        logger.error(f"Error during voice processing: {e}")
        await status_message.edit_text("Sorry, I ran into an error processing your voice note. Please try again.")

def main() -> None:
    """Start the bot."""
    # Build the application using the token
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Start the Bot using Polling
    logger.info("Bot started... Press Ctrl+C to stop.")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
