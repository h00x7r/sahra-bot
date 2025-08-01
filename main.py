import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from keep_alive import keep_alive

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage
user_data = {}  # {user_id: {'gender': str, 'age': int, 'status': str, 'partner': int or None}}
waiting_queue = []

# معلومات المطورين الذين يرون بيانات الطرف الآخر
DEVELOPERS = {
    5028799862,  # Khalil
    6832323842,  # Yaazed
}

# Constants (جميعها بالعربي)
WELCOME_MSG = "👋 أهلاً في سهرة بوت! دردش مع ناس مجهولين بشكل ممتع وسري 🔥"
PROFILE_INCOMPLETE = "يرجى إكمال ملفك الشخصي (الجنس والعمر) قبل بدء الدردشة."
SET_GENDER_PROMPT = "اختر جنسك:"
SET_AGE_PROMPT = "🧮 أدخل عمرك (رقم فقط):"
INVALID_AGE = "🚫 عمر غير صالح. يرجى إدخال رقم صحيح بين 1 و 100."
UPDATED_PROFILE = "✅ تم تحديث الملف الشخصي!"
START_SEARCH = "🔍 جاري البحث عن شريك..."
PARTNER_FOUND = "✅ تم العثور على شريك! ابدأ الدردشة الآن ✨"
CHAT_ENDED = "تم إنهاء الدردشة."
PARTNER_LEFT = "❗ غادر الشريك الدردشة."
EXIT_MSG = "👋 تم الخروج. ابدأ من جديد بـ /start."
NOT_IN_CHAT = "❗ أنت لست في دردشة نشطة."
ICE_BREAK_HINT = "💡 استخدم زر 'عززلي الحديث' لكسر الجليد إذا لم تعرف كيف تبدأ الحديث."

BUTTON_SET_GENDER = "👤 تحديد الجنس"
BUTTON_SET_AGE = "🎂 تحديد العمر"
BUTTON_START_CHAT = "🚀 بدء الدردشة"
BUTTON_EXIT = "❌ خروج"
BUTTON_MALE = "ذكر ♂️"
BUTTON_FEMALE = "أنثى ♀️"
BUTTON_UNKNOWN = "غير معروف 🤖"
BUTTON_SKIP = "🔁 تخطي الشريك"
BUTTON_END = "🛑 إنهاء الدردشة"
BUTTON_ICE_BREAK = "✨ عززلي الحديث"

CALLBACK_SET_GENDER = "set_gender"
CALLBACK_SET_AGE = "set_age"
CALLBACK_START_CHAT = "start_chat"
CALLBACK_EXIT = "exit"
CALLBACK_MALE = "male"
CALLBACK_FEMALE = "female"
CALLBACK_UNKNOWN = "unknown"
CALLBACK_SKIP = "skip"
CALLBACK_END = "end"
CALLBACK_ICE_BREAK = "ice_break"

# أسئلة كسر الجليد - 20 سؤال
ICE_BREAK_QUESTIONS = [
    "لو تقدر تسافر لأي مكان بالعالم، وين بتروح؟",
    "شو أكتر شيء بتحبه في نفسك؟",
    "لو كان عندك قوة خارقة، شو بتكون؟",
    "أفضل فيلم شفته مؤخراً؟",
    "إذا تقدر تعيش في أي زمن، أي زمن تختار؟",
    "شو أكتر أغنية ما بتملّ تسمعها؟",
    "لو قابلت شخص مشهور، مين حابب يكون؟",
    "شو هوايتك المفضلة؟",
    "لو بتقدر تغير اسمك، شو الاسم الجديد؟",
    "إذا كان عندك يوم كامل لنفسك، كيف بتقضيه؟",
    "شو أكتر شي بتتمنى تتعلمه؟",
    "لو صار معك مليون دولار، شو أول شي بتشتريه؟",
    "شو أكتر مكان بتحب تزوره في بلدك؟",
    "لو تكتب كتاب، شو بيكون عنوانه؟",
    "شو أكتر ذكرى مميزة عندك؟",
    "لو بتقدر تاكل أكلة وحدة طول حياتك، شو بتختار؟",
    "شو الشي اللي بيضحّكك دايماً؟",
    "لو بتقدر تلتقي بشخصية تاريخية، مين بتختار؟",
    "شو أحلى هدية تلقيتها؟",
    "لو بتقدر تغيّر العالم بحاجة وحدة، شو رح تكون؟"
]

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton(BUTTON_SET_GENDER, callback_data=CALLBACK_SET_GENDER)],
        [InlineKeyboardButton(BUTTON_SET_AGE, callback_data=CALLBACK_SET_AGE)],
        [InlineKeyboardButton(BUTTON_START_CHAT, callback_data=CALLBACK_START_CHAT)],
        [InlineKeyboardButton(BUTTON_EXIT, callback_data=CALLBACK_EXIT)],
        [InlineKeyboardButton("ℹ️ كيف يعمل البوت؟", callback_data="about_bot")],
        [InlineKeyboardButton("👨‍💻 تم التطوير بواسطة @h00x7r", url="https://t.me/h00x7r")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_gender_menu():
    keyboard = [
        [InlineKeyboardButton(BUTTON_MALE, callback_data=CALLBACK_MALE),
         InlineKeyboardButton(BUTTON_FEMALE, callback_data=CALLBACK_FEMALE)],
        [InlineKeyboardButton(BUTTON_UNKNOWN, callback_data=CALLBACK_UNKNOWN)],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_chat_menu():
    # زر التخطي والإنهاء تحت مربع الكتابة كلوحة أزرار ReplyKeyboard
    reply_keyboard = [
        [KeyboardButton(BUTTON_SKIP), KeyboardButton(BUTTON_END)],
    ]
    return ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

def get_inline_chat_menu():
    # لوحة أزرار إنلاين داخل الرسائل (التخطي والإنهاء)
    keyboard = [
        [InlineKeyboardButton(BUTTON_SKIP, callback_data=CALLBACK_SKIP),
         InlineKeyboardButton(BUTTON_END, callback_data=CALLBACK_END)],
        [InlineKeyboardButton(BUTTON_ICE_BREAK, callback_data=CALLBACK_ICE_BREAK)],
    ]
    return InlineKeyboardMarkup(keyboard)

def init_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {'gender': None, 'age': None, 'status': 'idle', 'partner': None}

def match_user(user_id):
    for i, waiting_id in enumerate(waiting_queue):
        if waiting_id != user_id:
            waiting_queue.pop(i)
            return waiting_id
    return None

def end_chat(user_id, notify_partner=True):
    partner = user_data[user_id]['partner']
    user_data[user_id]['status'] = 'idle'
    user_data[user_id]['partner'] = None
    if partner and notify_partner:
        user_data[partner]['status'] = 'idle'
        user_data[partner]['partner'] = None
        return partner
    return None

async def start(update: Update, context) -> None:
    user_id = update.effective_user.id
    init_user(user_id)
    await update.message.reply_text(WELCOME_MSG, reply_markup=get_main_menu())

async def stats(update: Update, context):
    count = len(user_data)
    await update.message.reply_text(f"👥 عدد الأشخاص الذين بدأوا البوت: {count}")

async def send_partner_info(user_id, partner_id, context):
    if user_id in DEVELOPERS:
        partner_obj = await context.bot.get_chat(partner_id)
        msg = (
            f"🚨 طرفك في الدردشة:\n"
            f"ID: {partner_obj.id}\n"
            f"Username: @{partner_obj.username if partner_obj.username else 'لا يوجد'}\n"
            f"Name: {partner_obj.first_name} {partner_obj.last_name or ''}"
        )
        await context.bot.send_message(user_id, msg)

async def button(update: Update, context) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    init_user(user_id)

    await query.answer()

    if data == "about_bot":
        about_text = """🤖 *طريقة عمل سهرة بوت:*

1. تختار جنسك وعمرك.
2. تضغط على 'بدء الدردشة'.
3. نبحث لك عن شريك متصل حاليًا.
4. تبدأ المحادثة مجهولًا تمامًا، وتقدر تنهي أو تخطي بأي وقت."""
        await query.edit_message_text(about_text, reply_markup=get_main_menu(), parse_mode="Markdown")
        return

    if data == CALLBACK_SET_GENDER:
        await query.edit_message_text(SET_GENDER_PROMPT, reply_markup=get_gender_menu())
    elif data in [CALLBACK_MALE, CALLBACK_FEMALE, CALLBACK_UNKNOWN]:
        user_data[user_id]['gender'] = BUTTON_MALE if data == CALLBACK_MALE else (BUTTON_FEMALE if data == CALLBACK_FEMALE else BUTTON_UNKNOWN)
        await query.edit_message_text(UPDATED_PROFILE, reply_markup=get_main_menu())
    elif data == CALLBACK_SET_AGE:
        user_data[user_id]['status'] = 'setting_age'
        await query.edit_message_text(SET_AGE_PROMPT)
    elif data == CALLBACK_START_CHAT:
        if not user_data[user_id]['gender'] or not user_data[user_id]['age']:
            await query.edit_message_text(PROFILE_INCOMPLETE, reply_markup=get_main_menu())
            return
        user_data[user_id]['status'] = 'waiting'
        await query.edit_message_text(START_SEARCH)
        partner = match_user(user_id)
        if partner:
            user_data[user_id]['partner'] = partner
            user_data[partner]['partner'] = user_id
            user_data[user_id]['status'] = 'chatting'
            user_data[partner]['status'] = 'chatting'

            user_gender = user_data[partner]['gender']
            user_age = user_data[partner]['age']
            partner_gender = user_data[user_id]['gender']
            partner_age = user_data[user_id]['age']

            await query.edit_message_text(f"{PARTNER_FOUND}\n\n👤 الجنس: {user_gender}\n🎂 العمر: {user_age}",
                                          reply_markup=get_inline_chat_menu())
            await context.bot.send_message(partner, f"{PARTNER_FOUND}\n\n👤 الجنس: {partner_gender}\n🎂 العمر: {partner_age}",
                                           reply_markup=get_inline_chat_menu())

            # أرسل بيانات الطرف الآخر للطرفين لو المطورين فقط
            await send_partner_info(user_id, partner, context)
            await send_partner_info(partner, user_id, context)
            
            # أرسل تلميح كسر الجليد لكل طرف عند بدء المحادثة
            await context.bot.send_message(user_id, ICE_BREAK_HINT)
            await context.bot.send_message(partner, ICE_BREAK_HINT)
        else:
            waiting_queue.append(user_id)
    elif data == CALLBACK_SKIP:
        if user_data[user_id]['status'] != 'chatting':
            await query.edit_message_text(NOT_IN_CHAT, reply_markup=get_main_menu())
            return
        partner = end_chat(user_id)
        await query.edit_message_text(CHAT_ENDED, reply_markup=get_main_menu())
        await context.bot.send_message(partner, PARTNER_LEFT, reply_markup=get_main_menu())
        user_data[user_id]['status'] = 'waiting'
        partner = match_user(user_id)
        if partner:
            user_data[user_id]['partner'] = partner
            user_data[partner]['partner'] = user_id
            user_data[user_id]['status'] = 'chatting'
            user_data[partner]['status'] = 'chatting'

            user_gender = user_data[partner]['gender']
            user_age = user_data[partner]['age']
            partner_gender = user_data[user_id]['gender']
            partner_age = user_data[user_id]['age']

            await context.bot.send_message(user_id, f"{PARTNER_FOUND}\n\n👤 الجنس: {user_gender}\n🎂 العمر: {user_age}",
                                           reply_markup=get_inline_chat_menu())
            await context.bot.send_message(partner, f"{PARTNER_FOUND}\n\n👤 الجنس: {partner_gender}\n🎂 العمر: {partner_age}",
                                           reply_markup=get_inline_chat_menu())

            # أرسل بيانات الطرف الآخر للطرفين لو المطورين فقط
            await send_partner_info(user_id, partner, context)
            await send_partner_info(partner, user_id, context)

            await context.bot.send_message(user_id, ICE_BREAK_HINT)
            await context.bot.send_message(partner, ICE_BREAK_HINT)
        else:
            waiting_queue.append(user_id)
            await context.bot.send_message(user_id, START_SEARCH)
    elif data == CALLBACK_END:
        if user_data[user_id]['status'] != 'chatting':
            await query.edit_message_text(NOT_IN_CHAT, reply_markup=get_main_menu())
            return
        partner = end_chat(user_id)
        await query.edit_message_text(CHAT_ENDED, reply_markup=get_main_menu())
        await context.bot.send_message(partner, CHAT_ENDED, reply_markup=get_main_menu())
    elif data == CALLBACK_EXIT:
        if user_data[user_id]['status'] == 'chatting':
            partner = end_chat(user_id)
            await context.bot.send_message(partner, PARTNER_LEFT, reply_markup=get_main_menu())
        if user_id in waiting_queue:
            waiting_queue.remove(user_id)
        del user_data[user_id]
        await query.edit_message_text(EXIT_MSG)
    elif data == CALLBACK_ICE_BREAK:
        # إرسال سؤال عشوائي من القائمة
        question = random.choice(ICE_BREAK_QUESTIONS)
        await context.bot.send_message(user_id, f"❓ سؤال كسر الجليد:\n{question}")

async def text_handler(update: Update, context) -> None:
    user_id = update.effective_user.id
    init_user(user_id)
    text = update.message.text

    # دعم أزرار لوحة المفاتيح لتخطي وإنهاء الدردشة
    if text == BUTTON_SKIP:
        if user_data[user_id]['status'] != 'chatting':
            await update.message.reply_text(NOT_IN_CHAT, reply_markup=get_main_menu())
            return
        partner = end_chat(user_id)
        await update.message.reply_text(CHAT_ENDED, reply_markup=get_main_menu())
        await context.bot.send_message(partner, PARTNER_LEFT, reply_markup=get_main_menu())
        user_data[user_id]['status'] = 'waiting'
        partner = match_user(user_id)
        if partner:
            user_data[user_id]['partner'] = partner
            user_data[partner]['partner'] = user_id
            user_data[user_id]['status'] = 'chatting'
            user_data[partner]['status'] = 'chatting'

            user_gender = user_data[partner]['gender']
            user_age = user_data[partner]['age']
            partner_gender = user_data[user_id]['gender']
            partner_age = user_data[user_id]['age']

            await context.bot.send_message(user_id, f"{PARTNER_FOUND}\n\n👤 الجنس: {user_gender}\n🎂 العمر: {user_age}",
                                           reply_markup=get_inline_chat_menu())
            await context.bot.send_message(partner, f"{PARTNER_FOUND}\n\n👤 الجنس: {partner_gender}\n🎂 العمر: {partner_age}",
                                           reply_markup=get_inline_chat_menu())

            # أرسل بيانات الطرف الآخر للطرفين لو المطورين فقط
            await send_partner_info(user_id, partner, context)
            await send_partner_info(partner, user_id, context)

            await context.bot.send_message(user_id, ICE_BREAK_HINT)
            await context.bot.send_message(partner, ICE_BREAK_HINT)
        else:
            waiting_queue.append(user_id)
            await context.bot.send_message(user_id, START_SEARCH)
        return

    if text == BUTTON_END:
        if user_data[user_id]['status'] != 'chatting':
            await update.message.reply_text(NOT_IN_CHAT, reply_markup=get_main_menu())
            return
        partner = end_chat(user_id)
        await update.message.reply_text(CHAT_ENDED, reply_markup=get_main_menu())
        await context.bot.send_message(partner, CHAT_ENDED, reply_markup=get_main_menu())
        return

    if user_data[user_id]['status'] == 'setting_age':
        try:
            age = int(text)
            if 1 <= age <= 100:
                user_data[user_id]['age'] = age
                user_data[user_id]['status'] = 'idle'
                await update.message.reply_text(UPDATED_PROFILE, reply_markup=get_main_menu())
            else:
                await update.message.reply_text(INVALID_AGE)
        except ValueError:
            await update.message.reply_text(INVALID_AGE)
    elif user_data[user_id]['status'] == 'chatting' and user_data[user_id]['partner']:
        await context.bot.send_message(user_data[user_id]['partner'], text)
    else:
        await update.message.reply_text(NOT_IN_CHAT, reply_markup=get_main_menu())

def main():
    keep_alive()
    token = os.getenv('BOT_TOKEN')
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("stats", stats))  # ✅ عرض عدد المستخدمين
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.run_polling()

if __name__ == '__main__':
    main()
