from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    Update
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

BOT_TOKEN = "8982855062:AAG6o14k6gufukoPsqWtvU__RjXX3XM7Qsw"

WEB_APP_URL = "http://localhost:5000"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="Open Ticket App",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ]
    ])

    await update.message.reply_text(
        "Open the ticket marketplace:",
        reply_markup=keyboard
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.run_polling()