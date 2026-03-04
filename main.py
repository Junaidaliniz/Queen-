import telebot
import sqlite3
import os
import time
from telebot import types

# --- CONFIGURATION ---
BOT_TOKEN = "8788622601:AAGZpH0FqTIo709jqzIu50rFAOdNXULUV2Q"
ADMINS = [7745665836]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True, num_threads=15)

# Flag mapping
FLAG_MAP = {
    "Kyrgyzstan": "🇰🇬", "Kazakhstan": "🇰🇿", "Russia": "🇷🇺", 
    "India": "🇮🇳", "USA": "🇺🇸", "UK": "🇬🇧", "Pakistan": "🇵🇰"
}

# ================= DATABASE SETUP =================
def init_db():
    conn = sqlite3.connect("bot_data.db", check_same_thread=False)
    cursor = conn.cursor()
    # Numbers Table
    cursor.execute("CREATE TABLE IF NOT EXISTS numbers (id INTEGER PRIMARY KEY, country TEXT, phone TEXT)")
    # Users Table (For Broadcast)
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    return conn

db = init_db()

def add_user(user_id):
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

def get_all_users():
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

def is_admin(uid): return uid in ADMINS

# ================= JOIN CHECK =================
def check_join(uid):
    required_channels = ["@AhmadEarningCenter", "@ahmadtricks"]
    for ch in required_channels:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status in ["left", "kicked"]: return False
        except: return False
    return True

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    add_user(m.chat.id) # User ko DB mein save karein
    if not check_join(m.chat.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/AhmadEarningCenter"))
        kb.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/ahmadtricks"))
        kb.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/ahmad_tricks"))
        kb.add(types.InlineKeyboardButton("✅ Verify", callback_data="verify"))
        bot.send_message(m.chat.id, "❌ <b>Join required channels first!</b>", reply_markup=kb)
        return
    show_countries(m.chat.id)

@bot.callback_query_handler(func=lambda c: c.data == "verify")
def verify(c):
    if check_join(c.from_user.id):
        bot.delete_message(c.message.chat.id, c.message.message_id)
        show_countries(c.from_user.id)
    else:
        bot.answer_callback_query(c.id, "❌ Still not joined!", show_alert=True)

# ================= USER PANEL =================
def show_countries(cid):
    cursor = db.cursor()
    cursor.execute("SELECT country, COUNT(*) FROM numbers GROUP BY country")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(cid, "❌ No numbers available right now.")
        return
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for country, count in rows:
        flag = FLAG_MAP.get(country, "🌍")
        buttons.append(types.InlineKeyboardButton(f"{flag} {country} ({count})", callback_data=f"get|{country}"))
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("🔄 Refresh List", callback_data="change"))
    bot.send_message(cid, "🌍 <b>Select Country:</b>", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("get|"))
def pick_country(c):
    country = c.data.split("|")[1]
    cursor = db.cursor()
    cursor.execute("SELECT id, phone FROM numbers WHERE country = ? LIMIT 1", (country,))
    res = cursor.fetchone()
    
    if res:
        db_id, phone = res
        cursor.execute("DELETE FROM numbers WHERE id = ?", (db_id,))
        db.commit()

        flag = FLAG_MAP.get(country, "🌍")
        kb = types.InlineKeyboardMarkup()
        # Side-by-side buttons
        kb.row(
            types.InlineKeyboardButton("🔄 Change Number", callback_data=f"get|{country}"),
            types.InlineKeyboardButton("🌍 Change Country", callback_data="change")
        )
        kb.row(types.InlineKeyboardButton("📱 OTP Group", url="https://t.me/ahmad_tricks"))

        text = (
            f"{flag} <b>Your Number ({flag} {country}):</b>\n\n"
            f"📞 <code>{phone}</code>\n\n"
            f"⏳ <b>Waiting for OTP...</b>\n"
            f"🔔 You'll get notified instantly!"
        )
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
    else:
        bot.answer_callback_query(c.id, "❌ Out of stock!", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "change")
def change(c):
    show_countries(c.message.chat.id)

# ================= ADMIN PANEL & BROADCAST =================
@bot.message_handler(commands=["admin"])
def admin(m):
    if not is_admin(m.chat.id): return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Add Numbers", "📋 Number List")
    kb.add("📣 Broadcast", "❌ Close")
    bot.send_message(m.chat.id, "🛠 <b>Admin Control Panel</b>", reply_markup=kb)

STATE = {}

@bot.message_handler(func=lambda m: m.text == "📣 Broadcast")
def bc_start(m):
    if not is_admin(m.chat.id): return
    STATE[m.chat.id] = "waiting_bc_msg"
    bot.send_message(m.chat.id, "📝 <b>Send the message you want to broadcast:</b>\n(Text, Photo, or Formatting supported)")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id) == "waiting_bc_msg")
def bc_send(m):
    if not is_admin(m.chat.id): return
    users = get_all_users()
    count = 0
    bot.send_message(m.chat.id, f"🚀 Sending message to {len(users)} users...")
    
    for u in users:
        try:
            bot.copy_message(u, m.chat.id, m.message_id)
            count += 1
            time.sleep(0.1) # Flood avoid karne ke liye
        except: pass
    
    bot.send_message(m.chat.id, f"✅ <b>Broadcast Completed!</b>\nSent to: {count} users.")
    del STATE[m.chat.id]

# --- Admin Add Numbers Logic ---
@bot.message_handler(func=lambda m: m.text == "➕ Add Numbers")
def add_num_start(m):
    if not is_admin(m.chat.id): return
    STATE[m.chat.id] = "waiting_country"
    bot.send_message(m.chat.id, "🌍 Send Country Name:")

@bot.message_handler(func=lambda m: STATE.get(m.chat.id) == "waiting_country")
def get_country_name(m):
    STATE[m.chat.id] = {"country": m.text}
    bot.send_message(m.chat.id, f"📄 Send .txt file for {m.text}:")

@bot.message_handler(content_types=["document"])
def handle_file(m):
    if m.chat.id not in STATE or not isinstance(STATE[m.chat.id], dict): return
    country = STATE[m.chat.id]["country"]
    file_info = bot.get_file(m.document.file_id)
    file_data = bot.download_file(file_info.file_path).decode("utf-8")
    nums = [n.strip() for n in file_data.splitlines() if n.strip()]
    
    cursor = db.cursor()
    cursor.executemany("INSERT INTO numbers (country, phone) VALUES (?, ?)", [(country, n) for n in nums])
    db.commit()
    bot.send_message(m.chat.id, f"✅ {len(nums)} numbers added to {country}!")
    del STATE[m.chat.id]

@bot.message_handler(func=lambda m: m.text == "📋 Number List")
def list_nums(m):
    if not is_admin(m.chat.id): return
    cursor = db.cursor()
    cursor.execute("SELECT country, COUNT(*) FROM numbers GROUP BY country")
    rows = cursor.fetchall()
    kb = types.InlineKeyboardMarkup()
    for country, count in rows:
        kb.add(types.InlineKeyboardButton(f"❌ Delete {country} ({count})", callback_data=f"del|{country}"))
    bot.send_message(m.chat.id, "Tap to delete stock:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del|"))
def delete_stock(c):
    country = c.data.split("|")[1]
    cursor = db.cursor()
    cursor.execute("DELETE FROM numbers WHERE country = ?", (country,))
    db.commit()
    bot.edit_message_text(f"✅ Deleted {country} stock", c.message.chat.id, c.message.message_id)

@bot.message_handler(func=lambda m: m.text == "❌ Close")
def close(m):
    bot.send_message(m.chat.id, "Admin Panel Closed", reply_markup=types.ReplyKeyboardRemove())

print("🤖 Bot is Online with Broadcast & DB...")
bot.infinity_polling()
