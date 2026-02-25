import os
import re
import json
import asyncio
import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8453214909:AAGPy_xyYcGUHcEWnjY0vFmul42gpdJMdM8"
ADMIN_ID = 7011937754
ADMINS = [7011937754]
DEFAULT_SMS_API = "https://api-node-js-new-production-b09a.up.railway.app/api?type=sms"

# =================== IN-MEMORY STORAGE ===================

numbers_db = {}
groups_db = {}
api_configs_db = {}
channels_db = {}
user_state = {}
user_watch = {}
seen_otps = set()
otp_counter = 0
db_id_counter = {"numbers": 0, "groups": 0, "apis": 0, "channels": 0}

COUNTRY_DETECT = {
    "Zimbabwe": {"name": "Zimbabwe", "code": "ZW", "flag": "\U0001f1ff\U0001f1fc"},
    "Venezuela": {"name": "Venezuela", "code": "VE", "flag": "\U0001f1fb\U0001f1ea"},
    "India": {"name": "India", "code": "IN", "flag": "\U0001f1ee\U0001f1f3"},
    "Russia": {"name": "Russia", "code": "RU", "flag": "\U0001f1f7\U0001f1fa"},
    "Kazakhstan": {"name": "Kazakhstan", "code": "KZ", "flag": "\U0001f1f0\U0001f1ff"},
    "Kyrgyzstan": {"name": "Kyrgyzstan", "code": "KG", "flag": "\U0001f1f0\U0001f1ec"},
    "USA": {"name": "USA", "code": "US", "flag": "\U0001f1fa\U0001f1f8"},
    "UK": {"name": "UK", "code": "GB", "flag": "\U0001f1ec\U0001f1e7"},
    "Pakistan": {"name": "Pakistan", "code": "PK", "flag": "\U0001f1f5\U0001f1f0"},
    "Brazil": {"name": "Brazil", "code": "BR", "flag": "\U0001f1e7\U0001f1f7"},
    "Nigeria": {"name": "Nigeria", "code": "NG", "flag": "\U0001f1f3\U0001f1ec"},
    "Kenya": {"name": "Kenya", "code": "KE", "flag": "\U0001f1f0\U0001f1ea"},
    "Indonesia": {"name": "Indonesia", "code": "ID", "flag": "\U0001f1ee\U0001f1e9"},
    "Philippines": {"name": "Philippines", "code": "PH", "flag": "\U0001f1f5\U0001f1ed"},
    "Mexico": {"name": "Mexico", "code": "MX", "flag": "\U0001f1f2\U0001f1fd"},
    "Colombia": {"name": "Colombia", "code": "CO", "flag": "\U0001f1e8\U0001f1f4"},
    "Bangladesh": {"name": "Bangladesh", "code": "BD", "flag": "\U0001f1e7\U0001f1e9"},
    "Turkey": {"name": "Turkey", "code": "TR", "flag": "\U0001f1f9\U0001f1f7"},
    "Egypt": {"name": "Egypt", "code": "EG", "flag": "\U0001f1ea\U0001f1ec"},
    "China": {"name": "China", "code": "CN", "flag": "\U0001f1e8\U0001f1f3"},
    "Guinea": {"name": "Guinea", "code": "GN", "flag": "\U0001f1ec\U0001f1f3"},
    "Ghana": {"name": "Ghana", "code": "GH", "flag": "\U0001f1ec\U0001f1ed"},
    "Tanzania": {"name": "Tanzania", "code": "TZ", "flag": "\U0001f1f9\U0001f1ff"},
    "Uganda": {"name": "Uganda", "code": "UG", "flag": "\U0001f1fa\U0001f1ec"},
    "Mozambique": {"name": "Mozambique", "code": "MZ", "flag": "\U0001f1f2\U0001f1ff"},
    "Zambia": {"name": "Zambia", "code": "ZM", "flag": "\U0001f1ff\U0001f1f2"},
    "Cambodia": {"name": "Cambodia", "code": "KH", "flag": "\U0001f1f0\U0001f1ed"},
    "Vietnam": {"name": "Vietnam", "code": "VN", "flag": "\U0001f1fb\U0001f1f3"},
    "Thailand": {"name": "Thailand", "code": "TH", "flag": "\U0001f1f9\U0001f1ed"},
    "Nepal": {"name": "Nepal", "code": "NP", "flag": "\U0001f1f3\U0001f1f5"},
    "Afghanistan": {"name": "Afghanistan", "code": "AF", "flag": "\U0001f1e6\U0001f1eb"},
    "Iraq": {"name": "Iraq", "code": "IQ", "flag": "\U0001f1ee\U0001f1f6"},
    "Iran": {"name": "Iran", "code": "IR", "flag": "\U0001f1ee\U0001f1f7"},
    "UAE": {"name": "UAE", "code": "AE", "flag": "\U0001f1e6\U0001f1ea"},
    "Argentina": {"name": "Argentina", "code": "AR", "flag": "\U0001f1e6\U0001f1f7"},
    "Peru": {"name": "Peru", "code": "PE", "flag": "\U0001f1f5\U0001f1ea"},
    "Chile": {"name": "Chile", "code": "CL", "flag": "\U0001f1e8\U0001f1f1"},
    "Ukraine": {"name": "Ukraine", "code": "UA", "flag": "\U0001f1fa\U0001f1e6"},
    "Germany": {"name": "Germany", "code": "DE", "flag": "\U0001f1e9\U0001f1ea"},
    "France": {"name": "France", "code": "FR", "flag": "\U0001f1eb\U0001f1f7"},
    "Italy": {"name": "Italy", "code": "IT", "flag": "\U0001f1ee\U0001f1f9"},
    "Spain": {"name": "Spain", "code": "ES", "flag": "\U0001f1ea\U0001f1f8"},
    "Canada": {"name": "Canada", "code": "CA", "flag": "\U0001f1e8\U0001f1e6"},
    "Australia": {"name": "Australia", "code": "AU", "flag": "\U0001f1e6\U0001f1fa"},
    "Japan": {"name": "Japan", "code": "JP", "flag": "\U0001f1ef\U0001f1f5"},
    "SouthAfrica": {"name": "South Africa", "code": "ZA", "flag": "\U0001f1ff\U0001f1e6"},
    "Malaysia": {"name": "Malaysia", "code": "MY", "flag": "\U0001f1f2\U0001f1fe"},
    "Singapore": {"name": "Singapore", "code": "SG", "flag": "\U0001f1f8\U0001f1ec"},
    "Morocco": {"name": "Morocco", "code": "MA", "flag": "\U0001f1f2\U0001f1e6"},
}

FLAG_MAP = {
    "Kyrgyzstan": "\U0001f1f0\U0001f1ec", "Kazakhstan": "\U0001f1f0\U0001f1ff",
    "Russia": "\U0001f1f7\U0001f1fa", "India": "\U0001f1ee\U0001f1f3",
    "USA": "\U0001f1fa\U0001f1f8", "UK": "\U0001f1ec\U0001f1e7",
    "Pakistan": "\U0001f1f5\U0001f1f0", "Zimbabwe": "\U0001f1ff\U0001f1fc",
    "Venezuela": "\U0001f1fb\U0001f1ea",
}


def get_flag(country):
    return FLAG_MAP.get(country, "\U0001f30d")


def is_admin(user_id):
    return user_id in ADMINS


# =================== STORAGE FUNCTIONS ===================

def get_number_stats():
    stats = {}
    for n in numbers_db.values():
        if n["status"] == "available":
            stats[n["country"]] = stats.get(n["country"], 0) + 1
    return [{"country": c, "count": cnt} for c, cnt in stats.items()]


def get_number_by_country(country):
    for n in numbers_db.values():
        if n["country"] == country and n["status"] == "available":
            return n
    return None


def bulk_create_numbers(country, phones):
    count = 0
    for phone in phones:
        db_id_counter["numbers"] += 1
        nid = db_id_counter["numbers"]
        numbers_db[nid] = {"id": nid, "country": country, "phone": phone.strip(), "status": "available", "assigned_to": None}
        count += 1
    return count


def delete_numbers_by_country(country):
    to_del = [k for k, v in numbers_db.items() if v["country"] == country]
    for k in to_del:
        del numbers_db[k]


def mark_number_assigned(nid, session_key):
    if nid in numbers_db:
        numbers_db[nid]["status"] = "assigned"
        numbers_db[nid]["assigned_to"] = session_key


def get_groups():
    return list(groups_db.values())


def get_active_groups():
    return [g for g in groups_db.values() if g.get("active", True)]


def add_group(group_id, title):
    db_id_counter["groups"] += 1
    gid = db_id_counter["groups"]
    groups_db[gid] = {"id": gid, "group_id": group_id, "title": title, "active": True}
    return groups_db[gid]


def remove_group(gid):
    groups_db.pop(gid, None)


def toggle_group(gid, active):
    if gid in groups_db:
        groups_db[gid]["active"] = active


def get_api_configs():
    return list(api_configs_db.values())


def add_api_config(name, url):
    db_id_counter["apis"] += 1
    aid = db_id_counter["apis"]
    api_configs_db[aid] = {"id": aid, "name": name, "url": url, "active": True}
    return api_configs_db[aid]


def remove_api_config(aid):
    api_configs_db.pop(aid, None)


def toggle_api_config(aid, active):
    if aid in api_configs_db:
        api_configs_db[aid]["active"] = active


def get_channels():
    return list(channels_db.values())


def get_active_channels():
    return [c for c in channels_db.values() if c.get("active", True)]


def add_channel(channel_id, channel_username, title):
    db_id_counter["channels"] += 1
    cid = db_id_counter["channels"]
    channels_db[cid] = {"id": cid, "channel_id": channel_id, "channel_username": channel_username, "title": title, "active": True}
    return channels_db[cid]


def remove_channel(cid):
    channels_db.pop(cid, None)


def toggle_channel(cid, active):
    if cid in channels_db:
        channels_db[cid]["active"] = active


# =================== OTP HELPERS ===================

def detect_country(panel):
    panel_lower = panel.lower()
    for key, value in COUNTRY_DETECT.items():
        if key.lower() in panel_lower:
            return value
    return {"name": "Unknown", "code": "XX", "flag": "\U0001f30d"}


def mask_phone_stars(phone):
    digits = re.sub(r'\D', '', phone)
    if len(digits) <= 6:
        return digits
    return f"{digits[:4]}****{digits[-4:]}"


def mask_phone_dots(phone):
    digits = re.sub(r'\D', '', phone)
    if len(digits) <= 4:
        return digits
    return f"{digits[:2]}\u2022\u2022{digits[-4:]}"


def get_service_icon(service):
    lower = service.lower()
    icons = {
        "whatsapp": "\U0001f7e2", "telegram": "\U0001f4e8", "tiktok": "\U0001f3b5",
        "netflix": "\U0001f534", "microsoft": "\U0001f7e6", "google": "\U0001f50d",
        "facebook": "\U0001f535", "instagram": "\U0001f4f7",
    }
    for k, v in icons.items():
        if k in lower:
            return v
    return "\U0001f4f1"


def get_service_short(service):
    lower = service.lower()
    shorts = {
        "whatsapp": "WA", "telegram": "TG", "tiktok": "TT", "netflix": "NF",
        "microsoft": "MS", "google": "GG", "facebook": "FB", "instagram": "IG",
        "twitter": "TW", "snapchat": "SC", "uber": "UB", "amazon": "AZ",
        "paypal": "PP", "discord": "DC", "signal": "SG", "viber": "VB",
    }
    for k, v in shorts.items():
        if k in lower:
            return v
    return service[:2].upper()


def extract_otp(message):
    patterns = [r'(\d{3}-\d{3})', r'(\d{6})', r'(\d{4,8})']
    for p in patterns:
        m = re.search(p, message)
        if m:
            return m.group(1)
    return None


def make_otp_key(entry):
    msg = str(entry.get("message", ""))[:30]
    return f"{entry['timestamp']}|{entry['phone']}|{msg}"


def build_group_message(otp, counter):
    country = detect_country(otp["panel"])
    masked = mask_phone_stars(otp["phone"])
    otp_code = extract_otp(otp["message"])
    svc_icon = get_service_icon(otp["sender"])

    text = f"{counter} {country['flag']} <b>New {country['name']} {otp['sender']} OTP!</b>\n\n"
    text += f"<blockquote>\U0001f570 Time: {otp['timestamp']}</blockquote>\n"
    text += f"<blockquote>{country['flag']} Country: {country['name']}</blockquote>\n"
    text += f"<blockquote>{svc_icon} Service: {otp['sender']}</blockquote>\n"
    text += f"<blockquote>\U0001f4de Number: {masked}</blockquote>\n"
    if otp_code:
        text += f"<blockquote>\U0001f511 OTP: {otp_code}</blockquote>\n"
    text += f"\n<blockquote>\U0001f4e9 Full Message:</blockquote>\n"
    text += f"<pre>{otp['message']}</pre>\n\n"
    text += f"<b>Powered By Queen o</b> \U0001f497"
    return text


def build_admin_message(otp):
    country = detect_country(otp["panel"])
    masked = mask_phone_dots(otp["phone"])
    svc_short = get_service_short(otp["sender"])

    text = f"{country['flag']} {country['code']} | {masked} | {svc_short}\n\n"
    text += f"Access: {otp['phone']}\n"
    text += f"Service: {otp['sender']}\n\n"
    text += f"Message:\n"
    text += f"<pre>{otp['message']}</pre>"
    return text


def build_user_message(otp, phone, country_name, flag):
    digits = re.sub(r'\D', '', phone)
    masked = f"{digits[:2]}\u2022\u2022{digits[-4:]}" if len(digits) > 4 else digits
    lower = otp["sender"].lower()
    svc = "WA" if "whatsapp" in lower else "TG" if "telegram" in lower else "TT" if "tiktok" in lower else otp["sender"][:2].upper()

    text = f"{flag} {country_name} | {masked} | {svc}\n\n"
    text += f"Access: {phone}\n"
    text += f"Service: {otp['sender']}\n\n"
    text += f"Message:\n"
    text += f"<pre>{otp['message']}</pre>"
    return text


GROUP_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("\U0001f3db Number", url="https://t.me/LegendNumber91"),
        InlineKeyboardButton("\U0001f47e DEVELOPER", url="https://t.me/Junaidniz786"),
    ],
    [
        InlineKeyboardButton("\U0001f4cb Channel", url="https://t.me/LegendTech92"),
        InlineKeyboardButton("\U0001f7e2 Whatsapp", url="https://whatsapp.com/channel/0029VbBbtd08V0tmjQXac13X"),
    ],
])


# =================== OTP POLLER ===================

async def fetch_otps_from_url(session, url):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            entries = []
            for row in data.get("aaData", []):
                if isinstance(row, list) and len(row) >= 5 and isinstance(row[0], str) and isinstance(row[4], str):
                    entries.append({
                        "timestamp": row[0],
                        "panel": str(row[1]),
                        "phone": str(row[2]),
                        "sender": str(row[3]),
                        "message": str(row[4]),
                    })
            return entries
    except Exception:
        return []


async def fetch_all_otps(session):
    urls = [DEFAULT_SMS_API]
    for cfg in api_configs_db.values():
        if cfg.get("active") and cfg["url"] not in urls:
            urls.append(cfg["url"])
    tasks = [fetch_otps_from_url(session, u) for u in urls]
    results = await asyncio.gather(*tasks)
    all_otps = []
    for r in results:
        all_otps.extend(r)
    return all_otps


async def otp_poller(bot_instance: Bot):
    global otp_counter
    initialized = False

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                otps = await fetch_all_otps(session)

                if not initialized:
                    for otp in otps:
                        seen_otps.add(make_otp_key(otp))
                    initialized = True
                    logger.info(f"OTP Poller initialized: {len(otps)} existing OTPs marked as seen")
                else:
                    for otp in otps:
                        key = make_otp_key(otp)
                        if key in seen_otps:
                            continue

                        seen_otps.add(key)
                        otp_counter += 1
                        logger.info(f"New OTP: {otp['phone']} from {otp['sender']} - forwarding")

                        group_text = build_group_message(otp, otp_counter)
                        for group in get_active_groups():
                            try:
                                await bot_instance.send_message(
                                    chat_id=group["group_id"], text=group_text,
                                    parse_mode=ParseMode.HTML, reply_markup=GROUP_KEYBOARD
                                )
                            except Exception as e:
                                logger.error(f"Group send error: {e}")

                        admin_text = build_admin_message(otp)
                        try:
                            await bot_instance.send_message(
                                chat_id=ADMIN_ID, text=admin_text, parse_mode=ParseMode.HTML
                            )
                        except Exception as e:
                            logger.error(f"Admin send error: {e}")

                        normalized = re.sub(r'\D', '', otp["phone"])
                        for watch_phone, watch_info in list(user_watch.items()):
                            watch_digits = re.sub(r'\D', '', watch_phone)
                            if normalized == watch_digits or normalized.endswith(watch_digits) or watch_digits.endswith(normalized):
                                user_text = build_user_message(otp, watch_info["phone"], watch_info["country"], watch_info["flag"])
                                try:
                                    await bot_instance.send_message(
                                        chat_id=watch_info["user_id"], text=user_text, parse_mode=ParseMode.HTML
                                    )
                                except Exception as e:
                                    logger.error(f"User send error: {e}")
                                del user_watch[watch_phone]
                                break

                if len(seen_otps) > 5000:
                    excess = list(seen_otps)[:len(seen_otps) - 2000]
                    for k in excess:
                        seen_otps.discard(k)

            except Exception as e:
                logger.error(f"Poller error: {e}")

            await asyncio.sleep(1.5)


# =================== FORCE JOIN ===================

async def check_force_join(bot_instance, user_id):
    active = get_active_channels()
    if not active:
        return True, []
    not_joined = []
    for ch in active:
        try:
            member = await bot_instance.get_chat_member(ch["channel_id"], user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return len(not_joined) == 0, not_joined


def build_force_join_message(not_joined):
    text = "\U0001f512 <b>Join Required Channels First!</b>\n\n"
    text += "You must join the following channels to use this bot:\n\n"
    buttons = []
    for ch in not_joined:
        text += f"\u2022 <b>{ch['title']}</b>\n"
        username = ch["channel_username"].replace("@", "")
        buttons.append([InlineKeyboardButton(f"\U0001f4e2 Join {ch['title']}", url=f"https://t.me/{username}")])
    text += "\nAfter joining, tap the button below:"
    buttons.append([InlineKeyboardButton("\u2705 I've Joined", callback_data="check_join")])
    return text, InlineKeyboardMarkup(buttons)


# =================== BOT HANDLERS ===================

async def start_cmd(update: Update, context):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        joined, not_joined = await check_force_join(context.bot, user_id)
        if not joined:
            text, kb = build_force_join_message(not_joined)
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            return

    stats = get_number_stats()

    buttons = []
    if not stats:
        buttons.append([InlineKeyboardButton("\U0001f504 Refresh List", callback_data="refresh")])
    else:
        for s in stats:
            flag = get_flag(s["country"])
            buttons.append([InlineKeyboardButton(f"{flag} {s['country']} ({s['count']})", callback_data=f"get|{s['country']}")])
        buttons.append([InlineKeyboardButton("\U0001f504 Refresh List", callback_data="refresh")])

    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")])

    text = "\u274c No numbers available right now." if not stats else "\U0001f30d <b>Select Country:</b>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))


async def callback_handler(update: Update, context):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if data == "check_join":
        joined, not_joined = await check_force_join(context.bot, user_id)
        if not joined:
            await query.answer("\u274c You haven't joined all channels yet!", show_alert=True)
            text, kb = build_force_join_message(not_joined)
            await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        await query.answer("\u2705 Verified! Welcome!")
        stats = get_number_stats()
        buttons = []
        if stats:
            for s in stats:
                flag = get_flag(s["country"])
                buttons.append([InlineKeyboardButton(f"{flag} {s['country']} ({s['count']})", callback_data=f"get|{s['country']}")])
        buttons.append([InlineKeyboardButton("\U0001f504 Refresh List", callback_data="refresh")])
        text = "\u274c No numbers available right now." if not stats else "\U0001f30d <b>Select Country:</b>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "refresh":
        await query.answer()
        stats = get_number_stats()
        buttons = []
        if stats:
            for s in stats:
                flag = get_flag(s["country"])
                buttons.append([InlineKeyboardButton(f"{flag} {s['country']} ({s['count']})", callback_data=f"get|{s['country']}")])
        buttons.append([InlineKeyboardButton("\U0001f504 Refresh List", callback_data="refresh")])
        if is_admin(user_id):
            buttons.append([InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")])
        text = "\u274c No numbers available right now." if not stats else "\U0001f30d <b>Select Country:</b>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("get|"):
        if not is_admin(user_id):
            joined, not_joined = await check_force_join(context.bot, user_id)
            if not joined:
                await query.answer("\u274c Join channels first!", show_alert=True)
                text, kb = build_force_join_message(not_joined)
                await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
                return

        country = data.split("|", 1)[1]
        number = get_number_by_country(country)
        if not number:
            await query.answer("\u274c Out of stock!", show_alert=True)
            return
        await query.answer()

        mark_number_assigned(number["id"], f"tg_{user_id}")
        flag = get_flag(country)

        user_watch[number["phone"]] = {"user_id": user_id, "phone": number["phone"], "country": country, "flag": flag}

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("\U0001f504 Change Number", callback_data=f"get|{country}"),
             InlineKeyboardButton("\U0001f30d Change Country", callback_data="change")],
            [InlineKeyboardButton("\U0001f4f1 OTP Group", url="https://t.me/+ZAtSLrWm7XMxNjc8")],
        ])
        text = (f"{flag} <b>Your Number ({flag} {country}):</b>\n\n"
                f"\U0001f4de <code>{number['phone']}</code>\n\n"
                f"\u23f3 <b>Waiting for OTP...</b>\n"
                f"\U0001f514 You'll get notified instantly!")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "change":
        await query.answer()
        stats = get_number_stats()
        buttons = []
        for s in stats:
            flag = get_flag(s["country"])
            buttons.append([InlineKeyboardButton(f"{flag} {s['country']} ({s['count']})", callback_data=f"get|{s['country']}")])
        buttons.append([InlineKeyboardButton("\U0001f504 Refresh List", callback_data="refresh")])
        if is_admin(user_id):
            buttons.append([InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")])
        await query.edit_message_text("\U0001f30d <b>Select Country:</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "owner_panel":
        if not is_admin(user_id):
            await query.answer("\u274c Access denied!", show_alert=True)
            return
        await query.answer()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2795 Add Number", callback_data="admin_add_number")],
            [InlineKeyboardButton("\U0001f4cb Number List", callback_data="admin_number_list")],
            [InlineKeyboardButton("\U0001f310 Add API", callback_data="admin_add_api")],
            [InlineKeyboardButton("\U0001f4e1 API List", callback_data="admin_api_list")],
            [InlineKeyboardButton("\u2795 Add Group", callback_data="admin_add_group")],
            [InlineKeyboardButton("\U0001f4c2 Group List", callback_data="admin_group_list")],
            [InlineKeyboardButton("\U0001f4e2 Add Channel", callback_data="admin_add_channel")],
            [InlineKeyboardButton("\U0001f4fa Channel List", callback_data="admin_channel_list")],
            [InlineKeyboardButton("\U0001f4e3 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="refresh")],
        ])
        await query.edit_message_text("\U0001f527 <b>Owner Panel:</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

    elif data == "admin_add_number":
        if not is_admin(user_id): return
        await query.answer()
        user_state[user_id] = {"step": "waiting_country"}
        await query.edit_message_text("\U0001f30d <b>Send Country Name:</b>\n\nType the country name and send it.", parse_mode=ParseMode.HTML)

    elif data == "admin_number_list":
        if not is_admin(user_id): return
        await query.answer()
        stats = get_number_stats()
        if not stats:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")]])
            await query.edit_message_text("\u274c No numbers in stock.", parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        buttons = []
        for s in stats:
            flag = get_flag(s["country"])
            buttons.append([InlineKeyboardButton(f"\u274c {flag} {s['country']} ({s['count']})", callback_data=f"del|{s['country']}")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text("\U0001f4cb <b>Current Stock:</b>\nTap to delete:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("del|"):
        if not is_admin(user_id): return
        country = data.split("|", 1)[1]
        delete_numbers_by_country(country)
        await query.answer(f"Deleted {country} stock!", show_alert=True)
        stats = get_number_stats()
        buttons = []
        if stats:
            for s in stats:
                flag = get_flag(s["country"])
                buttons.append([InlineKeyboardButton(f"\u274c {flag} {s['country']} ({s['count']})", callback_data=f"del|{s['country']}")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        text = "\u274c No numbers in stock." if not stats else "\U0001f4cb <b>Current Stock:</b>\nTap to delete:"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_add_api":
        if not is_admin(user_id): return
        await query.answer()
        user_state[user_id] = {"step": "waiting_api_name"}
        await query.edit_message_text("\U0001f310 <b>Add API</b>\n\nSend the API name:", parse_mode=ParseMode.HTML)

    elif data == "admin_api_list":
        if not is_admin(user_id): return
        await query.answer()
        configs = get_api_configs()
        if not configs:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2795 Add API", callback_data="admin_add_api")],
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")],
            ])
            await query.edit_message_text("\u274c No APIs configured.\n\nDefault API is being used.", parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        text = "\U0001f4e1 <b>API List:</b>\n\n"
        buttons = []
        for c in configs:
            status = "\U0001f7e2" if c["active"] else "\U0001f534"
            text += f"{status} <b>{c['name']}</b>\n<code>{c['url']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if c["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"api_toggle|{c['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"api_del|{c['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add API", callback_data="admin_add_api")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("api_toggle|"):
        if not is_admin(user_id): return
        aid = int(data.split("|")[1])
        if aid in api_configs_db:
            toggle_api_config(aid, not api_configs_db[aid]["active"])
        await query.answer("API status updated!")
        configs = get_api_configs()
        text = "\U0001f4e1 <b>API List:</b>\n\n"
        buttons = []
        for c in configs:
            status = "\U0001f7e2" if c["active"] else "\U0001f534"
            text += f"{status} <b>{c['name']}</b>\n<code>{c['url']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if c["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"api_toggle|{c['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"api_del|{c['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add API", callback_data="admin_add_api")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("api_del|"):
        if not is_admin(user_id): return
        aid = int(data.split("|")[1])
        remove_api_config(aid)
        await query.answer("API deleted!", show_alert=True)
        configs = get_api_configs()
        if not configs:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2795 Add API", callback_data="admin_add_api")],
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")],
            ])
            await query.edit_message_text("\u274c No APIs configured.", parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        text = "\U0001f4e1 <b>API List:</b>\n\n"
        buttons = []
        for c in configs:
            status = "\U0001f7e2" if c["active"] else "\U0001f534"
            text += f"{status} <b>{c['name']}</b>\n<code>{c['url']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if c["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"api_toggle|{c['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"api_del|{c['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add API", callback_data="admin_add_api")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_add_group":
        if not is_admin(user_id): return
        await query.answer()
        user_state[user_id] = {"step": "waiting_group_id"}
        await query.edit_message_text("\U0001f4c2 <b>Add Group</b>\n\nSend the Telegram Group ID (e.g. -1001234567890):", parse_mode=ParseMode.HTML)

    elif data == "admin_group_list":
        if not is_admin(user_id): return
        await query.answer()
        all_groups = get_groups()
        if not all_groups:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2795 Add Group", callback_data="admin_add_group")],
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")],
            ])
            await query.edit_message_text("\u274c No groups added.", parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        text = "\U0001f4c2 <b>Group List:</b>\n\n"
        buttons = []
        for g in all_groups:
            status = "\U0001f7e2" if g["active"] else "\U0001f534"
            text += f"{status} <b>{g['title']}</b>\nID: <code>{g['group_id']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if g["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"grp_toggle|{g['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"grp_del|{g['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add Group", callback_data="admin_add_group")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("grp_toggle|"):
        if not is_admin(user_id): return
        gid = int(data.split("|")[1])
        if gid in groups_db:
            toggle_group(gid, not groups_db[gid]["active"])
        await query.answer("Group status updated!")
        all_groups = get_groups()
        text = "\U0001f4c2 <b>Group List:</b>\n\n"
        buttons = []
        for g in all_groups:
            status = "\U0001f7e2" if g["active"] else "\U0001f534"
            text += f"{status} <b>{g['title']}</b>\nID: <code>{g['group_id']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if g["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"grp_toggle|{g['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"grp_del|{g['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add Group", callback_data="admin_add_group")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("grp_del|"):
        if not is_admin(user_id): return
        gid = int(data.split("|")[1])
        remove_group(gid)
        await query.answer("Group deleted!", show_alert=True)
        all_groups = get_groups()
        if not all_groups:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2795 Add Group", callback_data="admin_add_group")],
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")],
            ])
            await query.edit_message_text("\u274c No groups added.", parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        text = "\U0001f4c2 <b>Group List:</b>\n\n"
        buttons = []
        for g in all_groups:
            status = "\U0001f7e2" if g["active"] else "\U0001f534"
            text += f"{status} <b>{g['title']}</b>\nID: <code>{g['group_id']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if g["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"grp_toggle|{g['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"grp_del|{g['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add Group", callback_data="admin_add_group")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_add_channel":
        if not is_admin(user_id): return
        await query.answer()
        user_state[user_id] = {"step": "waiting_channel_id"}
        await query.edit_message_text("\U0001f4e2 <b>Add Force Join Channel</b>\n\nSend the Channel ID (e.g. -1001234567890):", parse_mode=ParseMode.HTML)

    elif data == "admin_channel_list":
        if not is_admin(user_id): return
        await query.answer()
        all_ch = get_channels()
        if not all_ch:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2795 Add Channel", callback_data="admin_add_channel")],
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")],
            ])
            await query.edit_message_text("\u274c No force join channels added.", parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        text = "\U0001f4fa <b>Force Join Channels:</b>\n\n"
        buttons = []
        for ch in all_ch:
            status = "\U0001f7e2" if ch["active"] else "\U0001f534"
            text += f"{status} <b>{ch['title']}</b>\n@{ch['channel_username']}\nID: <code>{ch['channel_id']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if ch["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"ch_toggle|{ch['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"ch_del|{ch['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add Channel", callback_data="admin_add_channel")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("ch_toggle|"):
        if not is_admin(user_id): return
        cid = int(data.split("|")[1])
        if cid in channels_db:
            toggle_channel(cid, not channels_db[cid]["active"])
        await query.answer("Channel status updated!")
        all_ch = get_channels()
        text = "\U0001f4fa <b>Force Join Channels:</b>\n\n"
        buttons = []
        for ch in all_ch:
            status = "\U0001f7e2" if ch["active"] else "\U0001f534"
            text += f"{status} <b>{ch['title']}</b>\n@{ch['channel_username']}\nID: <code>{ch['channel_id']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if ch["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"ch_toggle|{ch['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"ch_del|{ch['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add Channel", callback_data="admin_add_channel")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("ch_del|"):
        if not is_admin(user_id): return
        cid = int(data.split("|")[1])
        remove_channel(cid)
        await query.answer("Channel deleted!", show_alert=True)
        all_ch = get_channels()
        if not all_ch:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2795 Add Channel", callback_data="admin_add_channel")],
                [InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")],
            ])
            await query.edit_message_text("\u274c No force join channels added.", parse_mode=ParseMode.HTML, reply_markup=kb)
            return
        text = "\U0001f4fa <b>Force Join Channels:</b>\n\n"
        buttons = []
        for ch in all_ch:
            status = "\U0001f7e2" if ch["active"] else "\U0001f534"
            text += f"{status} <b>{ch['title']}</b>\n@{ch['channel_username']}\nID: <code>{ch['channel_id']}</code>\n\n"
            toggle = "\U0001f534 Deactivate" if ch["active"] else "\U0001f7e2 Activate"
            buttons.append([InlineKeyboardButton(toggle, callback_data=f"ch_toggle|{ch['id']}"),
                            InlineKeyboardButton("\U0001f5d1 Delete", callback_data=f"ch_del|{ch['id']}")])
        buttons.append([InlineKeyboardButton("\u2795 Add Channel", callback_data="admin_add_channel")])
        buttons.append([InlineKeyboardButton("\u2b05\ufe0f Back", callback_data="owner_panel")])
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin_broadcast":
        if not is_admin(user_id): return
        await query.answer()
        user_state[user_id] = {"step": "waiting_broadcast"}
        await query.edit_message_text("\U0001f4e3 <b>Send the message you want to broadcast to all groups:</b>", parse_mode=ParseMode.HTML)


async def text_handler(update: Update, context):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    if not state or not is_admin(user_id):
        return

    step = state["step"]

    if step == "waiting_country":
        country = update.message.text.strip()
        user_state[user_id] = {"step": "waiting_numbers", "country": country}
        await update.message.reply_text(
            f"\U0001f4c4 <b>Send phone numbers for {country}</b>\n\nOne number per line or send a .txt file:",
            parse_mode=ParseMode.HTML
        )

    elif step == "waiting_numbers":
        country = state["country"]
        nums = [n.strip() for n in update.message.text.split("\n") if n.strip()]
        if not nums:
            await update.message.reply_text("\u274c No valid numbers found.")
            return
        count = bulk_create_numbers(country, nums)
        user_state.pop(user_id, None)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2795 Add More", callback_data="admin_add_number"),
             InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")]
        ])
        await update.message.reply_text(f"\u2705 <b>{count} numbers added to {country}!</b>", parse_mode=ParseMode.HTML, reply_markup=kb)

    elif step == "waiting_api_name":
        user_state[user_id] = {"step": "waiting_api_url", "api_name": update.message.text.strip()}
        await update.message.reply_text("\U0001f517 <b>Now send the API URL:</b>", parse_mode=ParseMode.HTML)

    elif step == "waiting_api_url":
        add_api_config(state["api_name"], update.message.text.strip())
        user_state.pop(user_id, None)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("\U0001f4e1 API List", callback_data="admin_api_list"),
             InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")]
        ])
        await update.message.reply_text(f'\u2705 <b>API "{state["api_name"]}" added!</b>', parse_mode=ParseMode.HTML, reply_markup=kb)

    elif step == "waiting_channel_id":
        user_state[user_id] = {"step": "waiting_channel_username", "channel_id": update.message.text.strip()}
        await update.message.reply_text("\U0001f4dd <b>Send the channel username (e.g. @mychannel):</b>", parse_mode=ParseMode.HTML)

    elif step == "waiting_channel_username":
        user_state[user_id] = {**state, "step": "waiting_channel_title", "channel_username": update.message.text.strip().replace("@", "")}
        await update.message.reply_text("\U0001f4dd <b>Send a name for this channel:</b>", parse_mode=ParseMode.HTML)

    elif step == "waiting_channel_title":
        try:
            add_channel(state["channel_id"], state["channel_username"], update.message.text.strip())
            user_state.pop(user_id, None)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\U0001f4fa Channel List", callback_data="admin_channel_list"),
                 InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")]
            ])
            await update.message.reply_text(f'\u2705 <b>Force Join Channel "{update.message.text.strip()}" added!</b>', parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            user_state.pop(user_id, None)
            await update.message.reply_text("\u274c Failed to add channel.")

    elif step == "waiting_group_id":
        user_state[user_id] = {"step": "waiting_group_title", "group_id": update.message.text.strip()}
        await update.message.reply_text("\U0001f4dd <b>Send a name for this group:</b>", parse_mode=ParseMode.HTML)

    elif step == "waiting_group_title":
        try:
            add_group(state["group_id"], update.message.text.strip())
            user_state.pop(user_id, None)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("\U0001f4c2 Group List", callback_data="admin_group_list"),
                 InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")]
            ])
            await update.message.reply_text(f'\u2705 <b>Group "{update.message.text.strip()}" added!</b>', parse_mode=ParseMode.HTML, reply_markup=kb)
        except Exception:
            user_state.pop(user_id, None)
            await update.message.reply_text("\u274c Failed to add group.")

    elif step == "waiting_broadcast":
        user_state.pop(user_id, None)
        active = get_active_groups()
        sent = 0
        for g in active:
            try:
                await context.bot.copy_message(chat_id=g["group_id"], from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(f"\u2705 <b>Broadcast sent to {sent}/{len(active)} groups!</b>", parse_mode=ParseMode.HTML)


async def document_handler(update: Update, context):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    if not state or not is_admin(user_id) or state["step"] != "waiting_numbers":
        return

    try:
        country = state["country"]
        file = await update.message.document.get_file()
        file_bytes = await file.download_as_bytearray()
        text = file_bytes.decode("utf-8", errors="ignore")
        nums = [n.strip() for n in text.split("\n") if n.strip()]
        if not nums:
            await update.message.reply_text("\u274c No valid numbers in file.")
            return
        count = bulk_create_numbers(country, nums)
        user_state.pop(user_id, None)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2795 Add More", callback_data="admin_add_number"),
             InlineKeyboardButton("\U0001f527 Owner Panel", callback_data="owner_panel")]
        ])
        await update.message.reply_text(f"\u2705 <b>{count} numbers added to {country} from file!</b>", parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        await update.message.reply_text("\u274c Failed to process file.")


# =================== MAIN ===================

async def post_init(application):
    asyncio.create_task(otp_poller(application.bot))
    logger.info("OTP Poller started - polling every 1.5 seconds")


def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))

    logger.info("Telegram bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
