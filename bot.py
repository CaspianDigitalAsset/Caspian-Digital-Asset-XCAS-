import telebot
from telebot import types

# --- تنظیمات اصلی ربات ---
TOKEN = "8779335307:AAH0OA5m-RedEo0o4_d1YUXpkZCH0UfWIGw"
CHANNEL_USERNAME = "@xcaschannel"  # یوزرنیم کانال شما
ADMIN_ID = 92220977  # آیدی عددی ادمین

bot = telebot.TeleBot(TOKEN)

# --- پایگاه داده موقت (برای ذخیره اطلاعات کاربران) ---
# ساختار: { user_id: {"balance": 0, "referrals": 0, "referred_by": None} }
users_db = {}

# تنظیمات قابل تغییر توسط ادمین
settings = {
    "reward_per_referral": 10  # تعداد توکنی که به ازای هر رفرال داده می‌شود
}

def is_user_member(user_id):
    """بررسی اینکه آیا کاربر در کانال عضو است یا خیر"""
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # ثبت نام کاربر در صورت عدم وجود
    if user_id not in users_db:
        users_db[user_id] = {
            "balance": 0.0,
            "referrals": 0,
            "referred_by": None
        }

    # پردازش لینک رفرال (دعوت از دوستان)
    args = message.text.split()
    if len(args) > 1:
        inviter_id_str = args[1]
        if inviter_id_str.isdigit():
            inviter_id = int(inviter_id_str)
            # بررسی اینکه کاربر خودش را دعوت نکند و قبلاً دعوت نشده باشد
            if inviter_id != user_id and users_db[user_id]["referred_by"] is None:
                if inviter_id in users_db:
                    users_db[user_id]["referred_by"] = inviter_id
                    # افزایش آمار و بالانس معرف
                    users_db[inviter_id]["referrals"] += 1
                    reward = settings["reward_per_referral"]
                    users_db[inviter_id]["balance"] += reward
                    
                    # اطلاع‌رسانی به دعوت‌کننده
                    try:
                        bot.send_message(
                            inviter_id,
                            f"🎉 کاربر عزیز {first_name} با لینک اختصاصی شما وارد ربات شد!\n"
                            f"🎁 مقدار {reward} توکن به بالانس شما اضافه شد."
                        )
                    except Exception:
                        pass

    # بررسی عضویت اجباری در کانال
    if not is_user_member(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_slug = CHANNEL_USERNAME.replace('@', '')
        btn_join = types.InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{channel_slug}")
        btn_check = types.InlineKeyboardButton("✅ عضو شدم، بررسی کن", callback_data="check_membership")
        markup.add(btn_join)
        markup.add(btn_check)
        
        bot.send_message(
            user_id,
            f"سلام {first_name}! 👋\n\n"
            f"برای استفاده از ربات و دریافت لینک رفرال، ابتدا باید در کانال ما عضو شوید:\n"
            f"{CHANNEL_USERNAME}\n\n"
            f"پس از عضویت، روی دکمه زیر کلیک کنید.",
            reply_markup=markup
        )
        return

    # ارسال پنل کاربری در صورت عضویت
    send_main_menu(message.chat.id, user_id)

def send_main_menu(chat_id, user_id):
    """ارسال منوی اصلی و اطلاعات حساب کاربر"""
    user_data = users_db.get(user_id, {"balance": 0, "referrals": 0})
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = (
        f"📊 **پنل کاربری شما**\n\n"
        f"💰 موجودی توکن شما: `{user_data['balance']}` توکن\n"
        f"👥 تعداد زیرمجموعه‌های شما: `{user_data['referrals']}` نفر\n\n"
        f"🔗 **لینک دعوت اختصاصی شما:**\n`{ref_link}`\n\n"
        f"با ارسال این لینک به دوستان خود و عضویت آن‌ها در کانال، توکن پاداش بگیرید!"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 بروزرسانی حساب", callback_data="refresh_account"))
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def verify_membership(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_main_menu(call.message.chat.id, user_id)
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_account")
def refresh_account(call):
    user_id = call.from_user.id
    if not is_user_member(user_id):
        bot.answer_callback_query(call.id, "❌ ابتدا باید در کانال عضو بمانید!", show_alert=True)
        return
    bot.answer_callback_query(call.id, "به‌روزرسانی شد.")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_main_menu(call.message.chat.id, user_id)

# --- بخش مدیریت ادمین ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(user_id, "شما دسترسی ادمین ندارید.")
        return
    
    admin_text = (
        f"🛠 **پنل مدیریت ربات**\n\n"
        f"پاداش فعلی هر رفرال: `{settings['reward_per_referral']}` توکن\n"
        f"تعداد کل کاربران ثبت‌شده: `{len(users_db)}` نفر\n\n"
        f"برای تغییر پاداش از دستور زیر استفاده کنید:\n"
        f"`/setreward [عدد جدید]`"
    )
    bot.send_message(user_id, admin_text, parse_mode="Markdown")

@bot.message_handler(commands=['setreward'])
def set_reward(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        new_reward = float(args[1])
        settings["reward_per_referral"] = new_reward
        bot.send_message(user_id, f"✅ پاداش هر رفرال با موفقیت به {new_reward} تغییر یافت.")
    else:
        bot.send_message(user_id, "⚠️ لطفا مقدار جدید را به صورت عددی وارد کنید.\nمثال: `/setreward 15`", parse_mode="Markdown")

if __name__ == "__main__":
    print("Removing old webhooks...")
    bot.remove_webhook()
    print("Bot is running...")
    bot.infinity_polling()
