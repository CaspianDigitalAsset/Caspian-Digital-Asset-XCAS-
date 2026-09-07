import os
import io
import csv
import json
import telebot
from telebot import types
from js import Response

# --- تنظیمات اصلی ربات ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8779335307:AAH0OA5m-RedEo0o4_d1YUXpkZCH0UfWIGw")
CHANNEL_USERNAME = "@xcaschannel"  
ADMIN_ID = 92220977  

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# تنظیمات داینامیک پیش‌فرض (در صورت عدم وجود در دیتابیس)
settings = {
    "signup_reward": 0,          
    "reward_per_referral": 10,   
    "ref_milestone_count": 0,    
    "ref_milestone_bonus": 0,
    "announcement": None         
}

admin_states = {} 

TRANSLATIONS = {
    "fa": {
        "choose_lang": "Please select your language:",
        "lang_changed": "زبان با موفقیت به فارسی تغییر یافت.",
        "join_channel": "📢 عضویت در کانال",
        "check_membership": "✅ عضو شدم، بررسی کن",
        "not_member": "❌ شما هنوز در کانال عضو نشده‌اید!",
        "welcome": "سلام {name}! 👋\n\nبرای استفاده از ربات، ابتدا باید در کانال ما عضو شوید:\n{channel}\n\nپس از عضویت روی دکمه زیر کلیک کنید.",
        "ask_wallet": "💳 لطفاً آدرس کیف پول خود (ترجیحاً تون‌کیپر - Tonkeeper) را ارسال کنید:\n\n*(یا می‌توانید روی دکمه زیر کلیک کنید تا این مرحله را رد کرده و بعداً در تنظیمات وارد کنید)*",
        "skip_wallet": "⏭ رد کردن (ورود به پنل)",
        "wallet_saved": "✅ آدرس کیف پول شما با موفقیت ذخیره شد!",
        "wallet_skipped": "⚠️ ثبت کیف پول رد شد. هر زمان خواستید می‌توانید از بخش تنظیمات آن را وارد کنید.",
        "panel_title": "📊 **پنل کاربری شما**",
        "username": "👤 نام کاربری",
        "balance": "💰 موجودی توکن",
        "token_word": "توکن",
        "referrals": "👥 تعداد زیرمجموعه‌ها",
        "wallet": "💳 کیف پول",
        "not_set": "تنظیم نشده",
        "ref_link_text": "🔗 **لینک دعوت اختصاصی شما:**",
        "ref_desc": "با ارسال این لینک به دوستان خود و عضویت آن‌ها در کانال، توکن پاداش بگیرید!",
        "refresh": "🔄 بروزرسانی حساب",
        "settings": "⚙️ تنظیمات",
        "settings_title": "⚙️ **بخش تنظیمات**\n\nگزینه مورد نظر خود را انتخاب کنید:",
        "change_lang": "🌐 تغییر زبان",
        "set_wallet": "💳 ثبت/ویرایش کیف پول",
        "back_to_menu": "🔙 بازگشت به منوی اصلی",
        "enter_new_wallet": "لطفاً آدرس جدید کیف پول خود را ارسال کنید:",
        "ref_reward_msg": "🎉 کاربر عزیز {name} با لینک اختصاصی شما وارد ربات شد!\n🎁 مقدار {reward} توکن به بالانس شما اضافه شد.",
        "admin_panel": "🛠 **پنل مدیریت پیشرفته ربات**\n\n• پاداش عضویت اولیه: `{signup}` توکن\n• پاداش پایه هر رفرال: `{ref}` توکن\n• تعداد کل کاربران ثبت‌شده: `{users_count}` نفر\n\nاز دکمه‌های زیر استفاده کنید:",
        "adm_btn_signup": "🎁 تغییر پاداش عضویت",
        "adm_btn_ref": "👥 تغییر پاداش رفرال",
        "adm_btn_csv": "📊 خروجی اکسل (CSV)",
        "adm_btn_reset": "⚠️ ریست کامل ربات (حذف کاربران)",
        "adm_btn_announcement": "📢 تنظیم پیام ثابت/همگانی",
        "not_admin": "You are not admin."
    }
    # سایر زبان‌ها در صورت نیاز اضافه می‌شوند
}

def get_text(user_db_data, key, **kwargs):
    lang = user_db_data.get("lang", "fa") if user_db_data else "fa"
    trans = TRANSLATIONS.get(lang, TRANSLATIONS["fa"])
    text_template = trans.get(key, TRANSLATIONS["fa"].get(key, key))
    return text_template.format(**kwargs)

# --- توابع کار با دیتابیس کلودفلر (Cloudflare D1) ---
def get_user_from_db(env, user_id):
    query = "SELECT * FROM users WHERE user_id = ?"
    result = env.DB.prepare(query).bind(user_id).first()
    if result:
        return {
            "user_id": result.user_id,
            "first_name": result.first_name,
            "username": result.username,
            "balance": result.balance,
            "referrals": result.referrals,
            "referred_by": result.referred_by,
            "lang": result.lang,
            "wallet": result.wallet,
            "state": result.state
        }
    return None

def save_user_to_db(env, user_data):
    query = """
        INSERT INTO users (user_id, first_name, username, balance, referrals, referred_by, lang, wallet, state)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name=excluded.first_name,
            username=excluded.username,
            balance=excluded.balance,
            referrals=excluded.referrals,
            referred_by=excluded.referred_by,
            lang=excluded.lang,
            wallet=excluded.wallet,
            state=excluded.state;
    """
    env.DB.prepare(query).bind(
        user_data["user_id"],
        user_data.get("first_name", ""),
        user_data.get("username", ""),
        user_data.get("balance", 0.0),
        user_data.get("referrals", 0),
        user_data.get("referred_by"),
        user_data.get("lang", "fa"),
        user_data.get("wallet"),
        user_data.get("state")
    ).run()

def get_total_users_count(env):
    res = env.DB.prepare("SELECT COUNT(*) as count FROM users").first()
    return res.count if res else 0

def is_user_member(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# --- هندلرها و منطق ربات ---
@bot.message_handler(commands=['start'])
def handle_start(message, env):
    user_id = message.from_user.id
    user_data = get_user_from_db(env, user_id)
    
    if not user_data:
        initial_balance = float(settings["signup_reward"])
        user_data = {
            "user_id": user_id,
            "first_name": message.from_user.first_name or "No Name",
            "username": message.from_user.username or "",
            "balance": initial_balance,
            "referrals": 0,
            "referred_by": None,
            "lang": "fa",
            "wallet": None,
            "state": "selecting_lang"
        }

        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            inviter_id = int(args[1])
            if inviter_id != user_id:
                inviter_data = get_user_from_db(env, inviter_id)
                if inviter_data and not user_data["referred_by"]:
                    user_data["referred_by"] = inviter_id
                    inviter_data["referrals"] += 1
                    inviter_data["balance"] += settings["reward_per_referral"]
                    save_user_to_db(env, inviter_data)
                    
                    try:
                        msg_text = get_text(inviter_data, "ref_reward_msg", name=message.from_user.first_name, reward=settings["reward_per_referral"])
                        bot.send_message(inviter_id, msg_text)
                    except Exception:
                        pass
        save_user_to_db(env, user_data)
    else:
        user_data["first_name"] = message.from_user.first_name or "No Name"
        user_data["username"] = message.from_user.username or ""
        save_user_to_db(env, user_data)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="setlang_fa"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en")
    )
    bot.send_message(user_id, "Please select your language:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlang_"))
def process_language_selection(call, env):
    user_id = call.from_user.id
    lang_code = call.data.split("_")[1]
    
    user_data = get_user_from_db(env, user_id)
    if not user_data:
        user_data = {
            "user_id": user_id, "first_name": call.from_user.first_name or "", "username": call.from_user.username or "",
            "balance": float(settings["signup_reward"]), "referrals": 0, "referred_by": None, "wallet": None, "state": None
        }
    
    user_data["lang"] = lang_code
    save_user_to_db(env, user_data)
    bot.answer_callback_query(call.id, get_text(user_data, "lang_changed"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    check_channel_and_proceed(call, env)

def check_channel_and_proceed(call, env):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_data = get_user_from_db(env, user_id)

    if not is_user_member(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_slug = CHANNEL_USERNAME.replace('@', '')
        btn_join = types.InlineKeyboardButton(get_text(user_data, "join_channel"), url=f"https://t.me/{channel_slug}")
        btn_check = types.InlineKeyboardButton(get_text(user_data, "check_membership"), callback_data="check_membership")
        markup.add(btn_join, btn_check)
        
        bot.send_message(chat_id, get_text(user_data, "welcome", name=call.from_user.first_name, channel=CHANNEL_USERNAME), reply_markup=markup)
        return

    if not user_data.get("wallet"):
        ask_for_wallet(chat_id, user_id, env)
    else:
        send_main_menu(chat_id, user_id, env)

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def verify_membership(call, env):
    user_id = call.from_user.id
    user_data = get_user_from_db(env, user_id)
    if is_user_member(user_id):
        bot.answer_callback_query(call.id, "✅ OK!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        if not user_data.get("wallet"):
            ask_for_wallet(call.message.chat.id, user_id, env)
        else:
            send_main_menu(call.message.chat.id, user_id, env)
    else:
        bot.answer_callback_query(call.id, get_text(user_data, "not_member"), show_alert=True)

def ask_for_wallet(chat_id, user_id, env):
    user_data = get_user_from_db(env, user_id)
    user_data["state"] = "waiting_for_wallet"
    save_user_to_db(env, user_data)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(get_text(user_data, "skip_wallet"), callback_data="skip_wallet"))
    bot.send_message(chat_id, get_text(user_data, "ask_wallet"), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "skip_wallet")
def skip_wallet_step(call, env):
    user_id = call.from_user.id
    user_data = get_user_from_db(env, user_id)
    user_data["state"] = None
    save_user_to_db(env, user_data)
    bot.answer_callback_query(call.id, get_text(user_data, "wallet_skipped"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_main_menu(call.message.chat.id, user_id, env)

@bot.message_handler(func=lambda message, env: get_user_from_db(env, message.from_user.id) and get_user_from_db(env, message.from_user.id).get("state") == "waiting_for_wallet")
def save_wallet_address(message, env):
    user_id = message.from_user.id
    user_data = get_user_from_db(env, user_id)
    user_data["wallet"] = message.text.strip()
    user_data["state"] = None
    save_user_to_db(env, user_data)
    bot.send_message(message.chat.id, get_text(user_data, "wallet_saved"))
    send_main_menu(message.chat.id, user_id, env)

def send_main_menu(chat_id, user_id, env):
    user_data = get_user_from_db(env, user_id)
    username = f"@{user_data.get('username')}" if user_data.get('username') else get_text(user_data, "not_set")
    wallet = user_data.get("wallet") or get_text(user_data, "not_set")
    
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    token_w = get_text(user_data, 'token_word')
    
    text = (
        f"{get_text(user_data, 'panel_title')}\n\n"
        f"{get_text(user_data, 'username')}: `{username}`\n"
        f"{get_text(user_data, 'balance')}: `{user_data['balance']}` {token_w}\n"
        f"{get_text(user_data, 'referrals')}: `{user_data['referrals']}`\n"
        f"{get_text(user_data, 'wallet')}: `{wallet}`\n\n"
        f"{get_text(user_data, 'ref_link_text')}\n`{ref_link}`\n\n"
        f"{get_text(user_data, 'ref_desc')}"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(get_text(user_data, "refresh"), callback_data="refresh_account"),
        types.InlineKeyboardButton(get_text(user_data, "settings"), callback_data="open_settings")
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "refresh_account")
def refresh_account(call, env):
    user_id = call.from_user.id
    user_data = get_user_from_db(env, user_id)
    if not is_user_member(user_id):
        bot.answer_callback_query(call.id, get_text(user_data, "not_member"), show_alt=True)
        return
    bot.answer_callback_query(call.id, "Updated.")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_main_menu(call.message.chat.id, user_id, env)

# --- نقطه ورود کلودفلر (Cloudflare Worker Entry Point) ---
async def on_fetch(request, env, ctx):
    if request.method == "POST":
        try:
            req_data = await request.json()
            update = telebot.types.Update.de_json(json.dumps(req_data))
            
        
            # تزریق متغیر env به پردازشگر پیام‌ها
            bot.process_new_updates([update])
            return Response.new("OK", status=200)
        except Exception as e:
            return Response.new(str(e), status=500)
    
    return Response.new("Cloudflare Bot is running!", status=200)
