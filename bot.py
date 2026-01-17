from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler
import sqlite3
from datetime import datetime

import os
TOKEN = os.getenv("BOT_TOKEN")

# Database setup
conn = sqlite3.connect("engagement.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id INTEGER,
    username TEXT,
    timestamp TEXT
)
""")
conn.commit()

# Track messages
async def track_message(update, context):
    user = update.effective_user
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    timestamp = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?)",
        (user.id, full_name, timestamp)
    )
    conn.commit()

# Command: /count 2026-01-01 2026-01-10
async def count_messages(update, context):
    try:
        start, end = context.args
        cursor.execute("""
        SELECT username, COUNT(*)
        FROM messages
        WHERE timestamp BETWEEN ? AND ?
        GROUP BY username
        """, (start, end))

        result = cursor.fetchall()
        if not result:
            await update.message.reply_text("No data found.")
            return

        msg = "📊 Message Count:\n"
        for user, count in result:
            msg += f"- {user}: {count}\n"

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text(
            "Usage: /count YYYY-MM-DD YYYY-MM-DD"
        )

# App
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
app.add_handler(CommandHandler("count", count_messages))

app.run_polling()
