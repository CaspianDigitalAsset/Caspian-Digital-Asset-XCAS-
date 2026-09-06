import os
import io
import csv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# --- وب‌سرور داخلی برای پلتفرم Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# --- تنظیمات اصلی ربات ---
TOKEN = "8779335307:AAH0OA5m-RedEo0o4_d1YUXpkZCH0UfWIGw"
CHANNEL_USERNAME = "@xcaschannel"  
ADMIN_ID = 92220977  

bot = telebot.TeleBot(TOKEN)

# --- پایگاه داده و تنظیمات داینامیک ---
users_db = {}

settings = {
    "signup_reward": 0,          
    "reward_per_referral": 10,   
    "ref_milestone_count": 0,    
    "ref_milestone_bonus": 0,
    "announcement": None         # متن پیام ثابت عمومی
}

admin_states = {} 

# --- ترجمه کلمات به 6 زبان (به همراه متن‌های پنل ادمین) ---
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
        "admin_panel": "🛠 **پنل مدیریت پیشرفته ربات**\n\n• پاداش عضویت اولیه: `{signup}` توکن\n• پاداش پایه هر رفرال: `{ref}` توکن\n• ساختار تشویقی: هر `{m_count}` رفرال، مقدار `{m_bonus}` توکن اضافه\n• تعداد کل کاربران ثبت‌شده: `{users_count}` نفر\n\nاز دکمه‌های زیر استفاده کنید:",
        "adm_btn_signup": "🎁 تغییر پاداش عضویت",
        "adm_btn_ref": "👥 تغییر پاداش رفرال",
        "adm_btn_milestone": "⚙️ تنظیم ساختار رفرال",
        "adm_btn_csv": "📊 خروجی اکسل (CSV)",
        "adm_btn_html": "🌐 خروجی HTML",
        "adm_btn_reset": "⚠️ ریست کامل ربات (حذف کاربران)",
        "adm_btn_announcement": "📢 تنظیم پیام ثابت/همگانی",
        "not_admin": "You are not admin."
    },
    "en": {
        "choose_lang": "Please select your language:",
        "lang_changed": "Language successfully changed to English.",
        "join_channel": "📢 Join Channel",
        "check_membership": "✅ I've joined, check it",
        "not_member": "❌ You are not a member of the channel yet!",
        "welcome": "Hello {name}! 👋\n\nTo use the bot, you must first join our channel:\n{channel}\n\nClick the button below after joining.",
        "ask_wallet": "💳 Please send your wallet address (preferably Tonkeeper):\n\n*(Or click the button below to skip and set it later in settings)*",
        "skip_wallet": "⏭ Skip (Enter Panel)",
        "wallet_saved": "✅ Wallet address saved successfully!",
        "wallet_skipped": "⚠️ Wallet setup skipped. You can set it anytime from settings.",
        "panel_title": "📊 **Your User Panel**",
        "username": "👤 Username",
        "balance": "💰 Token Balance",
        "token_word": "tokens",
        "referrals": "👥 Referrals",
        "wallet": "💳 Wallet",
        "not_set": "Not Set",
        "ref_link_text": "🔗 **Your Exclusive Invite Link:**",
        "ref_desc": "Share this link with friends and earn tokens when they join the channel!",
        "refresh": "🔄 Refresh Account",
        "settings": "⚙️ Settings",
        "settings_title": "⚙️ **Settings Menu**\n\nChoose an option:",
        "change_lang": "🌐 Change Language",
        "set_wallet": "💳 Set/Edit Wallet",
        "back_to_menu": "🔙 Back to Main Menu",
        "enter_new_wallet": "Please send your new wallet address:",
        "ref_reward_msg": "🎉 User {name} joined via your invite link!\n🎁 {reward} tokens added to your balance.",
        "admin_panel": "🛠 **Advanced Admin Panel**\n\n• Signup Reward: `{signup}` tokens\n• Referral Reward: `{ref}` tokens\n• Milestone: Every `{m_count}` refs, `{m_bonus}` extra tokens\n• Total Registered Users: `{users_count}`\n\nUse buttons below:",
        "adm_btn_signup": "🎁 Change Signup Reward",
        "adm_btn_ref": "👥 Change Referral Reward",
        "adm_btn_milestone": "⚙️ Set Referral Milestone",
        "adm_btn_csv": "📊 Export CSV",
        "adm_btn_html": "🌐 Export HTML",
        "adm_btn_reset": "⚠️ Reset Bot (Clear Users)",
        "adm_btn_announcement": "📢 Set Announcement",
        "not_admin": "You are not admin."
    },
    "ru": {
        "choose_lang": "Please select your language:",
        "lang_changed": "Язык успешно изменен на русский.",
        "join_channel": "📢 Подписаться на канал",
        "check_membership": "✅ Я подписался, проверить",
        "not_member": "❌ Вы еще не подписаны на канал!",
        "welcome": "Привет, {name}! 👋\n\nЧтобы использовать бота, подпишитесь на наш канал:\n{channel}\n\nПосле подписки нажмите кнопку ниже.",
        "ask_wallet": "💳 Пожалуйста, отправьте адрес вашего кошелька (предпочтительно Tonkeeper):\n\n*(Или нажмите кнопку ниже, чтобы пропустить и настроить позже)*",
        "skip_wallet": "⏭ Пропустить (В меню)",
        "wallet_saved": "✅ Адрес кошелька успешно сохранен!",
        "wallet_skipped": "⚠️ Настройка кошелька пропущена. Вы можете указать его в настройках.",
        "panel_title": "📊 **Ваша панель управления**",
        "username": "👤 Имя пользователя",
        "balance": "💰 Баланс токенов",
        "token_word": "токенов",
        "referrals": "👥 Рефералы",
        "wallet": "💳 Кошелек",
        "not_set": "Не указан",
        "ref_link_text": "🔗 **Ваша реферальная ссылка:**",
        "ref_desc": "Поделитесь ссылкой с друзьями и получайте токены за их подписку!",
        "refresh": "🔄 Обновить",
        "settings": "⚙️ Настройки",
        "settings_title": "⚙️ **Меню настроек**\n\nВыберите опцию:",
        "change_lang": "🌐 Изменить язык",
        "set_wallet": "💳 Указать/Изменить кошелек",
        "back_to_menu": "🔙 Назад в меню",
        "enter_new_wallet": "Пожалуйста, отправьте новый адрес кошелька:",
        "ref_reward_msg": "🎉 Пользователь {name} присоединился по вашей ссылке!\n🎁 Вам начислено {reward} токенов.",
        "admin_panel": "🛠 **Панель администратора**\n\n• Награда за регистрацию: `{signup}`\n• Награда за реферала: `{ref}`\n• Всего пользователей: `{users_count}`\n\nИспользуйте кнопки:",
        "adm_btn_signup": "🎁 Изменить награду за рег.",
        "adm_btn_ref": "👥 Изменить награду реф.",
        "adm_btn_milestone": "⚙️ Настроить бонус",
        "adm_btn_csv": "📊 Экспорт CSV",
        "adm_btn_html": "🌐 Экспорт HTML",
        "adm_btn_reset": "⚠️ Сбросить бот",
        "adm_btn_announcement": "📢 Объявление",
        "not_admin": "You are not admin."
    },
    "ar": {
        "choose_lang": "Please select your language:",
        "lang_changed": "تم تغيير لغة التطبيق إلى العربية بنجاح.",
        "join_channel": "📢 اشتراك في القناة",
        "check_membership": "✅ لقد اشتركت، تحقق",
        "not_member": "❌ أنت لم تشترك في القناة بعد!",
        "welcome": "أهلاً بك {name}! 👋\n\nلاستخدام البوت، يجب عليك أولاً الاشتراك في قناتنا:\n{channel}\n\nاضغط على الزر أدناه بعد الاشتراك.",
        "ask_wallet": "💳 الرجاء إرسال عنوان محفظتك (يفضل Tonkeeper):\n\n*(أو يمكنك تخطي هذه الخطوة وإضافتها لاحقاً من الإعدادات)*",
        "skip_wallet": "⏭ تخطي (الدخول للقائمة)",
        "wallet_saved": "✅ تم حفظ عنوان المحفظة بنجاح!",
        "wallet_skipped": "⚠️ تم تخطي المحفظة. يمكنك إضافتها في أي وقت من الإعدادات.",
        "panel_title": "📊 **لوحة التحكم الخاصة بك**",
        "username": "👤 اسم المستخدم",
        "balance": "💰 رصيد الرموز",
        "token_word": "رمز",
        "referrals": "👥 عدد الإحالات",
        "wallet": "💳 المحفظة",
        "not_set": "غير محدد",
        "ref_link_text": "🔗 **رابط الدعوة الخاص بك:**",
        "ref_desc": "شارك هذا الرابط مع أصدقائك واكسب رموزاً عند اشتراكهم في القناة!",
        "refresh": "🔄 تحديث الحساب",
        "settings": "⚙️ الإعدادات",
        "settings_title": "⚙️ **قائمة الإعدادات**\n\nاختر ما يناسبك:",
        "change_lang": "🌐 تغيير اللغة",
        "set_wallet": "💳 تعيين/تعديل المحفظة",
        "back_to_menu": "🔙 العودة للقائمة الرئيسية",
        "enter_new_wallet": "الرجاء إرسال عنوان المحفظة الجديد:",
        "ref_reward_msg": "🎉 انضم المستخدم {name} عبر رابط الدعوة الخاص بك!\n🎁 تمت إضافة {reward} رموز إلى رصيدك.",
        "admin_panel": "🛠 **لوحة تحكم المشرف**\n\n• مكافأة التسجيل: `{signup}`\n• مكافأة الإحالة: `{ref}`\n• إجمالي المستخدمين: `{users_count}`\n\nاستخدم الأزرار أدناه:",
        "adm_btn_signup": "🎁 تغيير مكافأة التسجيل",
        "adm_btn_ref": "👥 تغيير مكافأة الإحالة",
        "adm_btn_milestone": "⚙️ إعدادات الإحالة",
        "adm_btn_csv": "📊 تصدير CSV",
        "adm_btn_html": "🌐 تصدير HTML",
        "adm_btn_reset": "⚠️ إعادة ضبط البوت",
        "adm_btn_announcement": "📢 تعيين رسالة عامة",
        "not_admin": "You are not admin."
    },
    "es": {
        "choose_lang": "Please select your language:",
        "lang_changed": "Idioma cambiado exitosamente a español.",
        "join_channel": "📢 Unirse al canal",
        "check_membership": "✅ Me he unido, verificar",
        "not_member": "❌ ¡Aún no te has unido al canal!",
        "welcome": "¡Hola {name}! 👋\n\nPara usar el bot, primero debes unirte a nuestro canal:\n{channel}\n\nHaz clic en el botón de abajo después de unirte.",
        "ask_wallet": "💳 Por favor envíe la dirección de su billetera (preferiblemente Tonkeeper):\n\n*(O haga clic abajo para omitir y configurarlo luego en ajustes)*",
        "skip_wallet": "⏭ Omitir (Ir al Panel)",
        "wallet_saved": "✅ ¡Dirección de billetera guardada con éxito!",
        "wallet_skipped": "⚠️ Configuración omitida. Puedes establecerla cuando quieras en ajustes.",
        "panel_title": "📊 **Tu Panel de Usuario**",
        "username": "👤 Nombre de usuario",
        "balance": "💰 Saldo de Tokens",
        "token_word": "tokens",
        "referrals": "👥 Referidos",
        "wallet": "💳 Billetera",
        "not_set": "No configurado",
        "ref_link_text": "🔗 **Tu enlace de invitación exclusivo:**",
        "ref_desc": "¡Comparte este enlace con amigos y gana tokens cuando se unan!",
        "refresh": "🔄 Actualizar",
        "settings": "⚙️ Ajustes",
        "settings_title": "⚙️ **Menú de Ajustes**\n\nSelecciona una opción:",
        "change_lang": "🌐 Cambiar Idioma",
        "set_wallet": "💳 Configurar/Editar Billetera",
        "back_to_menu": "🔙 Volver al Menú Principal",
        "enter_new_wallet": "Por favor, envíe la nueva dirección de su billetera:",
        "admin_panel": "🛠 **Panel de Administración**\n\n• Recompensa de registro: `{signup}`\n• Recompensa de referido: `{ref}`\n• Total de usuarios: `{users_count}`\n\nUsa los botones:",
        "adm_btn_signup": "🎁 Cambiar rec. registro",
        "adm_btn_ref": "👥 Cambiar rec. referido",
        "adm_btn_milestone": "⚙️ Config. hito",
        "adm_btn_csv": "📊 Exportar CSV",
        "adm_btn_html": "🌐 Exportar HTML",
        "adm_btn_reset": "⚠️ Reiniciar Bot",
        "adm_btn_announcement": "📢 Anuncio",
        "not_admin": "You are not admin."
    },
    "hi": {
        "choose_lang": "Please select your language:",
        "lang_changed": "भाषा सफलतापूर्वक हिंदी में बदल दी गई है।",
        "join_channel": "📢 चैनल से जुड़ें",
        "check_membership": "✅ मैंने जुड़ लिया है, जांचें",
        "not_member": "❌ आप अभी तक चैनल में शामिल नहीं हुए हैं!",
        "welcome": "नमस्ते {name}! 👋\n\nबॉट का उपयोग करने के लिए, पहले हमारे चैनल से जुड़ें:\n{channel}\n\nजुड़ने के बाद नीचे दिए गए बटन पर क्लिक करें।",
        "ask_wallet": "💳 कृपया अपना वॉलेट पता भेजें (प्राथमिकता Tonkeeper):\n\n*(या इसे छोड़ने और बाद में सेटिंग में जोड़ने के लिए नीचे दिए गए बटन पर क्लिक करें)*",
        "skip_wallet": "⏭ छोड़ें (पैनल में जाएं)",
        "wallet_saved": "✅ वॉलेट का पता सफलतापूर्वक सहेज लिया गया!",
        "wallet_skipped": "⚠️ वॉलेट सेटअप छोड़ दिया गया। आप इसे सेटिंग से कभी भी सेट कर सकते हैं.",
        "panel_title": "📊 **आपका यूजर पैनल**",
        "username": "👤 यूजरनेम",
        "balance": "💰 टोकन बैलेंस",
        "token_word": "टोकन",
        "referrals": "👥 रेफरल",
        "wallet": "💳 वॉलेट",
        "not_set": "सेट नहीं है",
        "ref_link_text": "🔗 **आपका विशेष आमंत्रण लिंक:**",
        "ref_desc": "इस लिंक को दोस्तों के साथ साझा करें और उनके जुड़ने पर टोकन कमाएं!",
        "refresh": "🔄 रिफ्रेश करें",
        "settings": "⚙️ सेटिंग",
        "settings_title": "⚙️ **सेटिंग्स मेनू**\n\nएक विकल्प चुनें:",
        "change_lang": "🌐 भाषा बदलें",
        "set_wallet": "💳 वॉलेट सेट/संपादित करें",
        "back_to_menu": "🔙 मुख्य मेनू पर जाएं",
        "enter_new_wallet": "कृपया अपना नया वॉलेट पता भेजें:",
        "admin_panel": "🛠 **एडमिन पैनल**\n\n• साइनअप रिवॉर्ड: `{signup}`\n• रेफरल रिवॉर्ड: `{ref}`\n• कुल उपयोगकर्ता: `{users_count}`\n\nबटन का उपयोग करें:",
        "adm_btn_signup": "🎁 साइनअप रिवॉर्ड बदलें",
        "adm_btn_ref": "👥 रेफरल रिवॉर्ड बदलें",
        "adm_btn_milestone": "⚙️ माइलस्टोन सेट करें",
        "adm_btn_csv": "📊 CSV एक्सपोर्ट",
        "adm_btn_html": "🌐 HTML एक्सपोर्ट",
        "adm_btn_reset": "⚠️ ربات را ریسیت کن",
        "adm_btn_announcement": "📢 घोषणा सेट करें",
        "not_admin": "You are not admin."
    }
}

def get_text(user_id, key, **kwargs):
    lang = users_db.get(user_id, {}).get("lang", "fa")
    text_template = TRANSLATIONS.get(lang, TRANSLATIONS["fa"]).get(key, TRANSLATIONS["fa"].get(key, key))
    return text_template.format(**kwargs)

def is_user_member(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    
    if user_id not in users_db:
        initial_balance = float(settings["signup_reward"])
        users_db[user_id] = {
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
        if len(args) > 1:
            inviter_id_str = args[1]
            if inviter_id_str.isdigit():
                inviter_id = int(inviter_id_str)
                if inviter_id != user_id and users_db[user_id]["referred_by"] is None:
                    if inviter_id in users_db:
                        users_db[user_id]["referred_by"] = inviter_id
                        users_db[inviter_id]["referrals"] += 1
                        
                        reward = settings["reward_per_referral"]
                        milestone_count = settings["ref_milestone_count"]
                        milestone_bonus = settings["ref_milestone_bonus"]
                        
                        if milestone_count > 0 and users_db[inviter_id]["referrals"] % milestone_count == 0:
                            reward += milestone_bonus

                        users_db[inviter_id]["balance"] += reward
                        try:
                            inviter_lang = users_db[inviter_id].get("lang", "fa")
                            msg_text = TRANSLATIONS[inviter_lang]["ref_reward_msg"].format(
                                name=message.from_user.first_name, reward=reward
                            )
                            bot.send_message(inviter_id, msg_text)
                        except Exception:
                            pass
    else:
        users_db[user_id]["first_name"] = message.from_user.first_name or "No Name"
        users_db[user_id]["username"] = message.from_user.username or ""
        if "balance" not in users_db[user_id]:
            users_db[user_id]["balance"] = float(settings["signup_reward"])
        if "referrals" not in users_db[user_id]:
            users_db[user_id]["referrals"] = 0
        if "lang" not in users_db[user_id]:
            users_db[user_id]["lang"] = "fa"

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="setlang_fa"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru"),
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
        types.InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="setlang_hi")
    )
    bot.send_message(user_id, "Please select your language:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlang_"))
def process_language_selection(call):
    user_id = call.from_user.id
    lang_code = call.data.split("_")[1]
    
    if user_id not in users_db:
        users_db[user_id] = {
            "user_id": user_id, 
            "first_name": call.from_user.first_name or "No Name", 
            "username": call.from_user.username or "", 
            "balance": float(settings["signup_reward"]), 
            "referrals": 0, 
            "referred_by": None, 
            "wallet": None
        }
    
    users_db[user_id]["lang"] = lang_code
    bot.answer_callback_query(call.id, get_text(user_id, "lang_changed"))
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    check_channel_and_proceed(call.message.chat.id, user_id)

def check_channel_and_proceed(chat_id, user_id):
    if not is_user_member(user_id):
        markup = types.InlineKeyboardMarkup()
        channel_slug = CHANNEL_USERNAME.replace('@', '')
        btn_join = types.InlineKeyboardButton(get_text(user_id, "join_channel"), url=f"https://t.me/{channel_slug}")
        btn_check = types.InlineKeyboardButton(get_text(user_id, "check_membership"), callback_data="check_membership")
        markup.add(btn_join)
        markup.add(btn_check)
        
        bot.send_message(
            chat_id,
            get_text(user_id, "welcome", name=bot.get_chat(user_id).first_name, channel=CHANNEL_USERNAME),
            reply_markup=markup
        )
        return

    if not users_db[user_id].get("wallet"):
        ask_for_wallet(chat_id, user_id)
    else:
        send_main_menu(chat_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def verify_membership(call):
    user_id = call.from_user.id
    if is_user_member(user_id):
        bot.answer_callback_query(call.id, "✅ OK!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        
        if not users_db[user_id].get("wallet"):
            ask_for_wallet(call.message.chat.id, user_id)
        else:
            send_main_menu(call.message.chat.id, user_id)
    else:
        bot.answer_callback_query(call.id, get_text(user_id, "not_member"), show_alert=True)

def ask_for_wallet(chat_id, user_id):
    users_db[user_id]["state"] = "waiting_for_wallet"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(get_text(user_id, "skip_wallet"), callback_data="skip_wallet"))
    bot.send_message(chat_id, get_text(user_id, "ask_wallet"), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "skip_wallet")
def skip_wallet_step(call):
    user_id = call.from_user.id
    users_db[user_id]["state"] = None
    bot.answer_callback_query(call.id, get_text(user_id, "wallet_skipped"))
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_main_menu(call.message.chat.id, user_id)

@bot.message_handler(func=lambda message: users_db.get(message.from_user.id, {}).get("state") == "waiting_for_wallet")
def save_wallet_address(message):
    user_id = message.from_user.id
    wallet_address = message.text.strip()
    
    users_db[user_id]["wallet"] = wallet_address
    users_db[user_id]["state"] = None
    
    bot.send_message(message.chat.id, get_text(user_id, "wallet_saved"))
    send_main_menu(message.chat.id, user_id)

def send_main_menu(chat_id, user_id):
    user_data = users_db.get(user_id, {"balance": 0, "referrals": 0, "wallet": None})
    username = f"@{user_data.get('username')}" if user_data.get('username') else get_text(user_id, "not_set")
    wallet = user_data.get("wallet") or get_text(user_id, "not_set")
    
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    token_w = get_text(user_id, 'token_word')
    
    announcement_text = f"\n\n📢 **اطلاعیه مهم:**\n{settings['announcement']}" if settings['announcement'] else ""

    text = (
        f"{get_text(user_id, 'panel_title')}\n\n"
        f"{get_text(user_id, 'username')}: `{username}`\n"
        f"{get_text(user_id, 'balance')}: `{user_data['balance']}` {token_w}\n"
        f"{get_text(user_id, 'referrals')}: `{user_data['referrals']}`\n"
        f"{get_text(user_id, 'wallet')}: `{wallet}`\n\n"
        f"{get_text(user_id, 'ref_link_text')}\n`{ref_link}`\n\n"
        f"{get_text(user_id, 'ref_desc')}"
        f"{announcement_text}"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(get_text(user_id, "refresh"), callback_data="refresh_account"),
        types.InlineKeyboardButton(get_text(user_id, "settings"), callback_data="open_settings")
    )
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "refresh_account")
def refresh_account(call):
    user_id = call.from_user.id
    if not is_user_member(user_id):
        bot.answer_callback_query(call.id, get_text(user_id, "not_member"), show_alert=True)
        return
    bot.answer_callback_query(call.id, "Updated.")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_main_menu(call.message.chat.id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "open_settings")
def open_settings_menu(call):
    user_id = call.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(get_text(user_id, "change_lang"), callback_data="setting_change_lang"),
        types.InlineKeyboardButton(get_text(user_id, "set_wallet"), callback_data="setting_set_wallet"),
        types.InlineKeyboardButton(get_text(user_id, "back_to_menu"), callback_data="back_to_main")
    )
    try:
        bot.edit_message_text(get_text(user_id, "settings_title"), call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        bot.send_message(call.message.chat.id, get_text(user_id, "settings_title"), reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "setting_change_lang")
def settings_change_lang(call):
    user_id = call.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="setlang_fa"),
        types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru"),
        types.InlineKeyboardButton("🇸🇦 العربية", callback_data="setlang_ar"),
        types.InlineKeyboardButton("🇪🇸 Español", callback_data="setlang_es"),
        types.InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="setlang_hi")
    )
    try:
        bot.edit_message_text("Please select your language:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception:
        bot.send_message(call.message.chat.id, "Please select your language:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "setting_set_wallet")
def settings_set_wallet(call):
    user_id = call.from_user.id
    users_db[user_id]["state"] = "waiting_for_wallet"
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, get_text(user_id, "enter_new_wallet"))

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_menu(call):
    user_id = call.from_user.id
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    send_main_menu(call.message.chat.id, user_id)

# --- بخش مدیریت پیشرفته (Admin Panel) ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        bot.send_message(user_id, get_text(user_id, "not_admin"))
        return
    
    admin_text = get_text(
        user_id, 
        "admin_panel", 
        signup=settings['signup_reward'], 
        ref=settings['reward_per_referral'], 
        m_count=settings['ref_milestone_count'], 
        m_bonus=settings['ref_milestone_bonus'], 
        users_count=len(users_db)
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(get_text(user_id, "adm_btn_signup"), callback_data="adm_set_signup"),
        types.InlineKeyboardButton(get_text(user_id, "adm_btn_ref"), callback_data="adm_set_ref"),
        types.InlineKeyboardButton(get_text(user_id, "adm_btn_milestone"), callback_data="adm_set_milestone"),
        types.InlineKeyboardButton(get_text(user_id, "adm_btn_csv"), callback_data="adm_export_csv"),
        types.InlineKeyboardButton(get_text(user_id, "adm_btn_html"), callback_data="adm_export_html"),
        types.InlineKeyboardButton(get_text(user_id, "adm_btn_announcement"), callback_data="adm_set_announcement"),
        types.InlineKeyboardButton(get_text(user_id, "adm_btn_reset"), callback_data="adm_reset_bot")
    )
    bot.send_message(user_id, admin_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_callbacks(call):
    user_id = call.from_user.id
    if user_id != ADMIN_ID:
        return
    
    action = call.data
    
    if action == "adm_set_signup":
        admin_states[user_id] = "waiting_signup_reward"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, get_text(user_id, "lang") == "fa" and "لطفاً مقدار جدید پاداش عضویت اولیه را (به صورت عدد) ارسال کنید:" or "Please send the new signup reward amount:")
    
    elif action == "adm_set_ref":
        admin_states[user_id] = "waiting_ref_reward"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, get_text(user_id, "lang") == "fa" and "لطفاً مقدار جدید پاداش پایه هر رفرال را (به صورت عدد) ارسال کنید:" or "Please send the new referral reward amount:")
        
    elif action == "adm_set_milestone":
        admin_states[user_id] = "waiting_milestone_config"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, get_text(user_id, "lang") == "fa" and "ساختار رفرال را به این شکل بفرستید (دو عدد با فاصله یا کاما):\nمثال: `5, 1`" or "Send milestone configuration (e.g., `5, 1`):")
        
    elif action == "adm_export_csv":
        bot.answer_callback_query(call.id, get_text(user_id, "lang") == "fa" and "در حال آماده‌سازی فایل اکسل..." or "Preparing CSV export...")
        send_csv_export(user_id)
        
    elif action == "adm_export_html":
        bot.answer_callback_query(call.id, get_text(user_id, "lang") == "fa" and "در حال آماده‌سازی فایل HTML..." or "Preparing HTML export...")
        send_html_export(user_id)

    elif action == "adm_reset_bot":
        markup = types.InlineKeyboardMarkup(row_width=2)
        if get_text(user_id, "lang") == "fa":
            markup.add(
                types.InlineKeyboardButton("✅ بله، کاملاً پاک شود", callback_data="adm_confirm_reset"),
                types.InlineKeyboardButton("❌ انصراف", callback_data="adm_cancel_reset")
            )
            msg = "⚠️ **آیا مطمئن هستید؟** با این کار اطلاعات تمام کاربران حذف شده و ربات ریست می‌شود."
        else:
            markup.add(
                types.InlineKeyboardButton("✅ Yes, Clear All", callback_data="adm_confirm_reset"),
                types.InlineKeyboardButton("❌ Cancel", callback_data="adm_cancel_reset")
            )
            msg = "⚠️ **Are you sure?** This will clear all user data and reset the bot."
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, msg, reply_markup=markup, parse_mode="Markdown")

    elif action == "adm_confirm_reset":
        users_db.clear()
        settings["announcement"] = None
        bot.answer_callback_query(call.id, "Bot reset successfully.")
        bot.send_message(user_id, get_text(user_id, "lang") == "fa" and "✅ تمام اطلاعات کاربران پاک شد و پایگاه داده خالی گردید." or "✅ All user data has been cleared and the database is empty.")

    elif action == "adm_cancel_reset":
        bot.answer_callback_query(call.id, "Cancelled.")
        bot.send_message(user_id, get_text(user_id, "lang") == "fa" and "❌ ریست ربات لغو گردید." or "❌ Bot reset cancelled.")

    elif action == "adm_set_announcement":
        markup = types.InlineKeyboardMarkup(row_width=1)
        if get_text(user_id, "lang") == "fa":
            markup.add(
                types.InlineKeyboardButton("📄 فقط نمایش در صفحه اصلی", callback_data="ann_type_menu"),
                types.InlineKeyboardButton("📢 ارسال همگانی به همه کاربران", callback_data="ann_type_broadcast"),
                types.InlineKeyboardButton("🗑 حذف اطلاعیه فعلی", callback_data="ann_type_clear")
            )
            msg = "انتخاب کنید این پیام چطور اعمال شود:"
        else:
            markup.add(
                types.InlineKeyboardButton("📄 Show in Main Menu Only", callback_data="ann_type_menu"),
                types.InlineKeyboardButton("📢 Broadcast to All Users", callback_data="ann_type_broadcast"),
                types.InlineKeyboardButton("🗑 Clear Current Announcement", callback_data="ann_type_clear")
            )
            msg = "Choose how to apply this message:"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ann_type_"))
def announcement_type_handler(call):
    user_id = call.from_user.id
    if user_id != ADMIN_ID:
        return
    
    action = call.data
    lang = get_text(user_id, "lang")
    if action == "ann_type_menu":
        admin_states[user_id] = "waiting_announcement_menu"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "لطفاً متن اطلاعیه را ارسال کنید تا در صفحه اصلی نمایش داده شود:" if lang == "fa" else "Please send the announcement text to show in the main menu:")
    elif action == "ann_type_broadcast":
        admin_states[user_id] = "waiting_announcement_broadcast"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "لطفاً متن پیام همگانی را ارسال کنید:" if lang == "fa" else "Please send the broadcast message text:")
    elif action == "ann_type_clear":
        settings["announcement"] = None
        bot.answer_callback_query(call.id, "Cleared.")
        bot.send_message(user_id, "✅ اطلاعیه پاک شد." if lang == "fa" else "✅ Announcement cleared.")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and admin_states.get(message.from_user.id))
def handle_admin_inputs(message):
    user_id = message.from_user.id
    state = admin_states.get(user_id)
    text = message.text.strip()
    lang = get_text(user_id, "lang")
    
    if state == "waiting_signup_reward":
        try:
            val = float(text)
            settings["signup_reward"] = val
            admin_states[user_id] = None
            bot.send_message(user_id, f"✅ پاداش عضویت به `{val}` تغییر یافت." if lang == "fa" else f"✅ Signup reward changed to `{val}`.")
        except ValueError:
            bot.send_message(user_id, "❌ لطفاً فقط یک عدد معتبر ارسال کنید." if lang == "fa" else "❌ Please send a valid number.")
            
    elif state == "waiting_ref_reward":
        try:
            val = float(text)
            settings["reward_per_referral"] = val
            admin_states[user_id] = None
            bot.send_message(user_id, f"✅ پاداش رفرال به `{val}` تغییر یافت." if lang == "fa" else f"✅ Referral reward changed to `{val}`.")
        except ValueError:
            bot.send_message(user_id, "❌ لطفاً فقط یک عدد معتبر ارسال کنید." if lang == "fa" else "❌ Please send a valid number.")
            
    elif state == "waiting_milestone_config":
        try:
            parts = text.replace(",", " ").split()
            count = int(parts[0])
            bonus = float(parts[1])
            settings["ref_milestone_count"] = count
            settings["ref_milestone_bonus"] = bonus
            admin_states[user_id] = None
            bot.send_message(user_id, f"✅ ساختار رفرال تنظیم شد." if lang == "fa" else "✅ Milestone config updated.")
        except Exception:
            bot.send_message(user_id, "❌ فرمت اشتباه است." if lang == "fa" else "❌ Invalid format.")

    elif state == "waiting_announcement_menu":
        settings["announcement"] = text
        admin_states[user_id] = None
        bot.send_message(user_id, "✅ اطلاعیه صفحه اصلی تنظیم شد." if lang == "fa" else "✅ Main menu announcement set.")

    elif state == "waiting_announcement_broadcast":
        admin_states[user_id] = None
        bot.send_message(user_id, f"🚀 در حال ارسال..." if lang == "fa" else f"🚀 Broadcasting...")
        success_count = 0
        for uid in users_db.keys():
            try:
                bot.send_message(uid, f"📢 **پیام مدیریت:**\n\n{text}", parse_mode="Markdown")
                success_count += 1
            except Exception:
                pass
        bot.send_message(user_id, f"✅ ارسال به {success_count} کاربر انجام شد." if lang == "fa" else f"✅ Broadcast sent to {success_count} users.")

def send_csv_export(admin_id):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "First Name", "Username", "Balance", "Referrals", "Language", "Wallet"])
    
    for uid, udata in users_db.items():
        writer.writerow([
            udata.get("user_id"),
            udata.get("first_name", ""),
            udata.get("username", ""),
            udata.get("balance", 0),
            udata.get("referrals", 0),
            udata.get("lang", "fa"),
            udata.get("wallet", "Not Set")
        ])
    
    output.seek(0)
    file_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    file_bytes.name = "users_report.csv"
    bot.send_document(admin_id, file_bytes, caption=f"📁 CSV Export (Total: {len(users_db)})")

def send_html_export(admin_id):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Users Report</title>
        <style>
            body {{ font-family: Tahoma, sans-serif; direction: rtl; background: #f4f4f9; padding: 20px; }}
            h2 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; background: #fff; margin-top: 15px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h2>گزارش کامل کاربران ربات (مجموع اعضا: {len(users_db)})</h2>
        <table>
            <tr>
                <th>شناسه کاربری (ID)</th>
                <th>نام</th>
                <th>نام کاربری</th>
                <th>موجودی توکن</th>
                <th>تعداد رفرال</th>
                <th>زبان</th>
                <th>کیف پول</th>
            </tr>
    """
    
    for uid, udata in users_db.items():
        uname = f"@{udata.get('username')}" if udata.get("username") else "ندارد"
        wlt = udata.get("wallet") or "ثبت نشده"
        html_content += f"""
            <tr>
                <td>{udata.get("user_id")}</td>
                <td>{udata.get("first_name", "بدون نام")}</td>
                <td>{uname}</td>
                <td>{udata.get("balance", 0)}</td>
                <td>{udata.get("referrals", 0)}</td>
                <td>{udata.get("lang", "fa")}</td>
                <td>{wlt}</td>
            </tr>
        """
        
    html_content += """
        </table>
    </body>
    </html>
    """
    
    file_bytes = io.BytesIO(html_content.encode('utf-8'))
    file_bytes.name = "users_report.html"
    bot.send_document(admin_id, file_bytes, caption=f"🌐 HTML Export (Total: {len(users_db)})")

if __name__ == "__main__":
    print("Removing old webhooks...")
    bot.remove_webhook()
    print("Bot is running with full features and updates...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
