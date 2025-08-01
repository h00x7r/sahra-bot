import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from keep_alive import keep_alive

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage
user_data = {}  # {user_id: {'gender': str, 'age': int, 'status': str, 'partner': int or None}}
waiting_queue = []

# Icebreaker questions
icebreaker_questions = [
    "لو قدرت تسافر لأي مكان بالعالم هلأ، وين بتروح؟",
    "إذا كان فيك تمتلك قدرة خارقة، شو بتختار؟",
    "أغرب شي صار معك الأسبوع الماضي؟",
    "شو أكتر فيلم أثر فيك وما نسيته؟",
    "مين أول شخص بتخطر على بالك وقت تضحك؟",
    "إذا رجعناك لزمن الطفولة، شو أول شي بتعمله؟",
    "لو كان فيك تغير اسمك، شو بتختار؟",
    "أكتر أكلة بتحبها وما بتمل منها؟",
    "لو كتبت كتاب عن حياتك، شو راح تسميه؟",
    "أكتر صفة بتحبها بشخصيتك؟",
    "لو فيك تسأل أي شخص بالعالم سؤال، مين وشو بتسأل؟",
    "شو أغرب عادة عندك؟",
    "لو عطيتك بطاقة مفتوحة تشتري شي، شو بتشتري؟",
    "إذا كنت بتمثل بفيلم، أي نوع أفلام بتختار؟",
    "لو صار فيك تعيش يوم بمكان تاني، وين بتروح؟",
    "أكتر شي بيخليك تضحك فجأة؟",
    "هل بتعتبر حالك شخص صباحي ولا مسائي؟",
    "لو كنت شخصية كرتونية، مين بتكون؟",
    "شو الأغنية اللي دايمًا بتعيدها وما تمل منها؟",
    "لو كان فيك تعيش بفترة تاريخية قديمة، أي وحدة بتختار؟"
]

# Constants
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
ICEBREAKER_HINT = "💡 يمكنك استخدام زر 'عززلي الحديث' الموجود أسفل الشاشة لبدء الحديث!"

# Button Texts
BUTTON_SET_GENDER = "👤 تحديد الجنس"
BUTTON_SET_AGE = "🎂 تحديد العمر"
BUTTON_START_CHAT = "🚀 بدء الدردشة"
BUTTON_EXIT = "❌ خروج"
BUTTON_MALE = "ذكر ♂️"
BUTTON_FEMALE = "أنثى ♀️"
BUTTON_UNKNOWN = "غير معروف 🤖"
BUTTON_SKIP = "🔁 تخطي الشريك"
BUTTON_END = "🛑 إنهاء الدردشة"
BUTTON_ICEBREAKER = "💬 عززلي الحديث"

CALLBACK_SET_GENDER = "set_gender"
CALLBACK_SET_AGE = "set_age"
CALLBACK_START_CHAT = "start_chat"
CALLBACK_EXIT = "exit"
CALLBACK_MALE = "male"
CALLBACK_FEMALE = "female"
CALLBACK_UNKNOWN = "unknown"
CALLBACK_SKIP = "skip"
CALLBACK_END = "end"
CALLBACK_ICEBREAKER = "icebreaker"

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
    keyboard = [
        [InlineKeyboardButton(BUTTON_SKIP, callback_data=CALLBACK_SKIP),
         InlineKeyboardButton(BUTTON_END, callback_data=CALLBACK_END)],
        [InlineKeyboardButton(BUTTON_ICEBREAKER, callback_data=CALLBACK_ICEBREAKER)],
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

async def start(update: Update, context):
    user_id = update.effective_user.id
    init_user(user_id)
    await update.message.reply_text(WELCOME_MSG, reply_markup=get_main_menu())

async def stats(update: Update, context):
    count = len(user_data)
    await update.message.reply_text(f"👥 عدد الأشخاص الذين بدأوا البوت: {count}")

async def button(update: Update, context):
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

            await query.edit_message_text(f"{PARTNER_FOUND}\n\n👤 الجنس: {user_gender}\n🎂 العمر: {user_age}\n\n{ICEBREAKER_HINT}", reply_markup=get_chat_menu())
            await context.bot.send_message(partner, f"{PARTNER_FOUND}\n\n👤 الجنس: {partner_gender}\n🎂 العمر: {partner_age}\n\n{ICEBREAKER_HINT}", reply_markup=get_chat_menu())
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
            await context.bot.send_message(user_id, f"{PARTNER_FOUND}\n\n👤 الجنس: {user_gender}\n🎂 العمر: {user_age}\n\n{ICEBREAKER_HINT}", reply_markup=get_chat_menu())
            await context.bot.send_message(partner, f"{PARTNER_FOUND}\n\n👤 الجنس: {partner_gender}\n🎂 العمر: {partner_age}\n\n{ICEBREAKER_HINT}", reply_markup=get_chat_menu())
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
    elif data == CALLBACK_ICEBREAKER:
        question = random.choice(icebreaker_questions)
        partner = user_data[user_id].get('partner')
        if partner:
            await context.bot.send_message(user_id, f"❓ {question}")
            await context.bot.send_message(partner, f"❓ {question}")

async def text_handler(update: Update, context):
    user_id = update.effective_user.id
    init_user(user_id)
    if user_data[user_id]['status'] == 'setting_age':
        try:
            age = int(update.message.text)
            if 1 <= age <= 100:
                user_data[user_id]['age'] = age
                user_data[user_id]['status'] = 'idle'
                await update.message.reply_text(UPDATED_PROFILE, reply_markup=get_main_menu())
            else:
                await update.message.reply_text(INVALID_AGE)
        except ValueError:
            await update.message.reply_text(INVALID_AGE)
    elif user_data[user_id]['status'] == 'chatting' and user_data[user_id]['partner']:
        await context.bot.send_message(user_data[user_id]['partner'], update.message.text)
    else:
        await update.message.reply_text(NOT_IN_CHAT, reply_markup=get_main_menu())

def main():
    keep_alive()
    token = os.getenv('BOT_TOKEN')
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.run_polling()

if __name__ == '__main__':
    main()
