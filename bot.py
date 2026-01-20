import os
import sqlite3
from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")  # Railway Environment Variable
TIMEZONE = ZoneInfo("Asia/Phnom_Penh")

# ======================
# DATABASE SETUP
# ======================
conn = sqlite3.connect("engagement.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id INTEGER,
    name TEXT,
    timestamp TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY,
    name TEXT
)
""")

conn.commit()

# ======================
# UTIL FUNCTIONS
# ======================
def is_weekend():
    return datetime.now(TIMEZONE).weekday() >= 5  # Sat=5, Sun=6

# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = f"{user.first_name} {user.last_name or ''}".strip()

    cursor.execute(
        "INSERT OR IGNORE INTO admins VALUES (?, ?)",
        (user.id, name)
    )
    conn.commit()

    await update.message.reply_text(
        "✅ You are registered to receive weekend engagement summaries."
    )

async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_weekend():
        return

    if not update.effective_user:
        return

    user = update.effective_user
    name = f"{user.first_name} {user.last_name or ''}".strip()
    timestamp = datetime.now(TIMEZONE).isoformat()

    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?)",
        (user.id, name, timestamp)
    )
    conn.commit()

async def weekend_summary(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""
    SELECT name, COUNT(*)
    FROM messages
    WHERE timestamp >= datetime('now', '-2 days')
    GROUP BY name
    ORDER BY COUNT(*) DESC
    """)

    rows = cursor.fetchall()

    if not rows:
        message = "📊 Weekend Engagement Summary\n\nNo messages recorded."
    else:
        message = "📊 Weekend Engagement Summary\n\n"
        for name, count in rows:
            message += f"- {name}: {count}\n"

    cursor.execute("SELECT user_id FROM admins")
    admins = cursor.fetchall()

    for (admin_id,) in admins:
        await context.bot.send_message(
            chat_id=admin_id,
            text=message
        )

# ======================
# MAIN APP
# ======================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))

    # Sunday 6:00 PM Cambodia Time
    app.job_queue.run_daily(
        weekend_summary,
        time=time(hour=18, minute=0, tzinfo=TIMEZONE),
        days=(6,)
    )

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
