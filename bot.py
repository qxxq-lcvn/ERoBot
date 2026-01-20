import os
import sqlite3
from datetime import datetime
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set")

# Database
conn = sqlite3.connect("engagement.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id INTEGER,
    name TEXT,
    timestamp TEXT
)
""")
conn.commit()

# Track messages
async def track_message(update, context):
    user = update.effective_user
    name = f"{user.first_name} {user.last_name or ''}".strip()
    timestamp = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?)",
        (user.id, name, timestamp)
    )
    conn.commit()

# /count command
async def count_messages(update, context):
    try:
        start, end = context.args

        cursor.execute("""
        SELECT name, COUNT(*)
        FROM messages
        WHERE timestamp BETWEEN ? AND ?
        GROUP BY name
        """, (start, end))

        rows = cursor.fetchall()
        if not rows:
            await update.message.reply_text("No data found.")
            return

        msg = "📊 Message Count:\n"
        for name, count in rows:
            msg += f"- {name}: {count}\n"

        await update.message.reply_text(msg)

    except Exception:
        await update.message.reply_text(
            "Usage: /count YYYY-MM-DD YYYY-MM-DD"
        )

# App
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
app.add_handler(CommandHandler("count", count_messages))

app.run_polling()
