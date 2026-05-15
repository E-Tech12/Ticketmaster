import os
import json
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

load_dotenv()

# States for conversation
SEARCHING, SELECTING_EVENT, SHOWING_SEATS, CONFIRMING = range(4)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FLASK_URL = os.getenv("FLASK_URL", "https://ticketmaster-2tr2.onrender.com/")

async def start(update: Update, context):
    await update.message.reply_text(
        "🎟️ *Welcome to Ticket Resale Marketplace!*\n\n"
        "I can help you find tickets and select seats for your favorite events.\n\n"
        "🔍 *Tell me what event you're looking for:*\n"
        "Examples: 'BTS concert', 'NBA finals', 'Taylor Swift', 'World Cup'",
        parse_mode='Markdown'
    )
    return SEARCHING

async def search_events(update: Update, context):
    query = update.message.text
    context.user_data['search_query'] = query
    
    await update.message.reply_text(f"🔎 Searching for '{query}'...")
    
    try:
        response = requests.get(f"{FLASK_URL}/api/search", params={'q': query}, timeout=10)
        data = response.json()
        events = data.get('events', [])
        
        if not events:
            await update.message.reply_text(
                "❌ No events found. Try a different search term.\n\n"
                "Example: 'BTS', 'The Weeknd', 'Champions League'"
            )
            return SEARCHING
        
        context.user_data['events'] = events
        
        keyboard = []
        for event in events[:10]:
            button_text = f"🎤 {event['name'][:40]} - {event['date']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"event_{event['id']}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        await update.message.reply_text(
            f"✅ Found {len(events)} events!\n\nSelect one to view seats:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECTING_EVENT
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error searching events: {str(e)}\nPlease try again.")
        return SEARCHING

async def event_selected(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Search cancelled. Use /start to begin again.")
        return ConversationHandler.END
    
    event_id = query.data.replace("event_", "")
    
    # Find selected event
    selected = None
    for event in context.user_data.get('events', []):
        if event['id'] == event_id:
            selected = event
            break
    
    if not selected:
        await query.edit_message_text("❌ Event not found. Please search again.")
        return SEARCHING
    
    context.user_data['selected_event'] = selected
    
    # Create WebApp button for seat selection
    seatmap_url = f"{FLASK_URL}/seatmap/{event_id}"
    
    keyboard = [[
        InlineKeyboardButton(
            "🎯 View & Select Interactive Seats",
            web_app=WebAppInfo(url=seatmap_url)
        )
    ]]
    
    message = (
        f"🎤 *{selected['name']}*\n\n"
        f"📅 *Date:* {selected['date']}\n"
        f"📍 *Venue:* {selected['venue']}\n"
        f"🎟️ *Price Range:* {selected.get('price_range', 'Check website')}\n\n"
        f"✨ Click the button below to see the interactive seat map!\n"
        f"*You can select up to 4 seats.*"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return SHOWING_SEATS

async def handle_webapp_data(update: Update, context):
    """Receive seat selection from Web App"""
    try:
        seat_data = json.loads(update.message.web_app_data.data)
        context.user_data['selected_seats'] = seat_data
        
        event = context.user_data.get('selected_event', {})
        
        confirmation_msg = (
            f"✅ *Seats Selected!*\n\n"
            f"🎤 Event: {event.get('name', 'Unknown')}\n"
            f"📅 Date: {event.get('date', 'TBA')}\n\n"
            f"🎯 *Your Selections:*\n"
            f"• Section: {seat_data['section']}\n"
            f"• Row: {seat_data['row']}\n"
            f"• Seats: {', '.join(seat_data['seats'])}\n"
            f"• Quantity: {seat_data['quantity']}\n\n"
            f"⚠️ *Note:* This is a demo. No actual payment required.\n\n"
            f"Do you want to confirm these seats?"
        )
        
        keyboard = [[
            InlineKeyboardButton("✅ Confirm Reservation", callback_data="final_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_reservation")
        ]]
        
        await update.message.reply_text(
            confirmation_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return CONFIRMING
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing seat selection: {str(e)}")
        return SHOWING_SEATS

async def confirm_reservation(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_reservation":
        await query.edit_message_text(
            "❌ Reservation cancelled.\n\nUse /start to search for new events."
        )
        return ConversationHandler.END
    
    # Final confirmation
    event = context.user_data.get('selected_event', {})
    seats = context.user_data.get('selected_seats', {})
    
    # Generate a demo ticket
    ticket_message = (
        f"🎫 *RESERVATION CONFIRMED!* 🎫\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎤 *Event:* {event.get('name', 'Unknown')}\n"
        f"📅 *Date:* {event.get('date', 'TBA')}\n"
        f"📍 *Venue:* {event.get('venue', 'TBA')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Seat Details:*\n"
        f"   Section: {seats.get('section', 'N/A')}\n"
        f"   Row: {seats.get('row', 'N/A')}\n"
        f"   Seats: {', '.join(seats.get('seats', []))}\n"
        f"   Quantity: {seats.get('quantity', 0)}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *This is a demo ticket*\n"
        f"✨ No payment required\n\n"
        f"📱 Show this message at the venue (just for fun!)\n\n"
        f"Use /start to book more tickets!"
    )
    
    await query.edit_message_text(
        ticket_message,
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text("❌ Operation cancelled. Use /start to begin again.")
    return ConversationHandler.END

async def help_command(update: Update, context):
    help_text = (
        "🎟️ *Ticket Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/cancel - Cancel current operation\n\n"
        "*How it works:*\n"
        "1️⃣ Search for an event\n"
        "2️⃣ Select from the list\n"
        "3️⃣ Click the button to open interactive seat map\n"
        "4️⃣ Click on available seats (green)\n"
        "5️⃣ Confirm your selection\n"
        "6️⃣ Get your demo ticket!\n\n"
        "*Note:* This is a demo app. No real payments or ticket purchases happen here."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_events)],
            SELECTING_EVENT: [CallbackQueryHandler(event_selected)],
            SHOWING_SEATS: [MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data)],
            CONFIRMING: [CallbackQueryHandler(confirm_reservation)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('help', help_command)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('help', help_command))
    
    print("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()