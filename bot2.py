from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes, CallbackQueryHandler
)
import datetime

# Стани
MENU, CHOOSING, AUTO_NAME, AUTO_FLAT, AUTO_CAR, AUTO_PHONE, AUTO_DATE, GUEST_NAME, GUEST_FLAT, GUEST_GUESTNAME, GUEST_PHONE, GUEST_DATE = range(12)

SECURITY_CHAT_ID = 1653501821  # заміни на реальний chat_id охорони
REQUEST_COUNTER = 0  # глобальний лічильник заявок

def save_to_log(text):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {text}\n")

# --- Головне меню ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("▶️ Почати", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ласкаво просимо! Оберіть дію:", reply_markup=reply_markup)
    return MENU

async def menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data in ["menu", "new_request"]:
        keyboard = [
            [InlineKeyboardButton("🚗 Пропуск АВТО", callback_data="auto")],
            [InlineKeyboardButton("👤 Пропуск Гостя", callback_data="guest")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=query.from_user.id, text="Оберіть тип пропуску:", reply_markup=reply_markup)
        return CHOOSING

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "auto":
        await context.bot.send_message(chat_id=query.from_user.id, text="Введіть Ваше Ім’я та Прізвище:")
        return AUTO_NAME
    elif query.data == "guest":
        await context.bot.send_message(chat_id=query.from_user.id, text="Введіть Ваше Ім’я та Прізвище:")
        return GUEST_NAME
# --- Авто ---
async def auto_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["auto_name"] = update.message.text
    await update.message.reply_text("Введіть номер квартири:")
    return AUTO_FLAT

async def auto_flat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["auto_flat"] = update.message.text
    await update.message.reply_text("Введіть номер авто:")
    return AUTO_CAR

async def auto_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["auto_car"] = update.message.text
    keyboard = [[KeyboardButton("📱 Поділитись номером телефону", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Натисніть кнопку, щоб поділитись номером телефону:", reply_markup=reply_markup)
    return AUTO_PHONE

async def auto_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["auto_phone"] = update.message.contact.phone_number
    else:
        context.user_data["auto_phone"] = "не надано"

    keyboard = [
        [InlineKeyboardButton("Сьогодні", callback_data="date_auto_today")],
        [InlineKeyboardButton("Завтра", callback_data="date_auto_tomorrow")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть дату заїзду:", reply_markup=reply_markup)
    return AUTO_DATE

async def auto_date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "date_auto_today":
        context.user_data["auto_date"] = datetime.date.today().strftime("%d.%m.%Y")
    elif query.data == "date_auto_tomorrow":
        context.user_data["auto_date"] = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")

    return await finish_auto(query, context)

async def finish_auto(query_or_update, context: ContextTypes.DEFAULT_TYPE):
    global REQUEST_COUNTER
    REQUEST_COUNTER += 1
    request_id = REQUEST_COUNTER

    requester_id = query_or_update.from_user.id if hasattr(query_or_update, "from_user") else query_or_update.message.from_user.id
    username = f"@{query_or_update.from_user.username}" if query_or_update.from_user.username else "немає логіну"

    summary = (
        f"🚗 Пропуск АВТО\n"
        f"Номер заявки: #{request_id}\n"
        f"Номер авто: {context.user_data['auto_car']}\n"
        f"Дата заїзду: {context.user_data['auto_date']}\n\n"
        f"Заявник:\n"
        f"👤 Ім’я: {context.user_data['auto_name']}\n"
        f"🏠 Квартира: {context.user_data['auto_flat']}\n"
        f"📱 Телефон: {context.user_data.get('auto_phone', 'не надано')}\n"
        f"💬 Telegram: {username}"
    )

    keyboard = [[InlineKeyboardButton("📤 Створити ще одну заявку", callback_data="new_request")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_id = query_or_update.message.chat_id if hasattr(query_or_update, "message") else query_or_update.from_user.id
    await context.bot.send_message(chat_id=chat_id, text="✅ Дані збережено та передано охороні.\n\n" + summary, reply_markup=reply_markup)

    # кнопка для охоронця з ID заявника
    keyboard_security = [[InlineKeyboardButton("✅ Прийнято", callback_data=f"accepted_{requester_id}")]]
    reply_markup_security = InlineKeyboardMarkup(keyboard_security)
    await context.bot.send_message(chat_id=SECURITY_CHAT_ID, text=summary, reply_markup=reply_markup_security)

    save_to_log(summary)
    return MENU
# --- Гостя ---
async def guest_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["guest_name"] = update.message.text
    await update.message.reply_text("Введіть номер квартири:")
    return GUEST_FLAT

async def guest_flat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["guest_flat"] = update.message.text
    await update.message.reply_text("Введіть Прізвище та Ім’я гостя:")
    return GUEST_GUESTNAME

async def guest_guestname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["guest_guestname"] = update.message.text
    keyboard = [[KeyboardButton("📱 Поділитись номером телефону", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Натисніть кнопку, щоб поділитись номером телефону:", reply_markup=reply_markup)
    return GUEST_PHONE

async def guest_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["guest_phone"] = update.message.contact.phone_number
    else:
        context.user_data["guest_phone"] = "не надано"

    keyboard = [
        [InlineKeyboardButton("Сьогодні", callback_data="date_guest_today")],
        [InlineKeyboardButton("Завтра", callback_data="date_guest_tomorrow")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть дату входу:", reply_markup=reply_markup)
    return GUEST_DATE

async def guest_date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "date_guest_today":
        context.user_data["guest_date"] = datetime.date.today().strftime("%d.%m.%Y")
    elif query.data == "date_guest_tomorrow":
        context.user_data["guest_date"] = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")

    return await finish_guest(query, context)

async def finish_guest(query_or_update, context: ContextTypes.DEFAULT_TYPE):
    global REQUEST_COUNTER
    REQUEST_COUNTER += 1
    request_id = REQUEST_COUNTER

    requester_id = query_or_update.from_user.id if hasattr(query_or_update, "from_user") else query_or_update.message.from_user.id
    username = f"@{query_or_update.from_user.username}" if query_or_update.from_user.username else "немає логіну"

    summary = (
        f"👤 Пропуск Гостя\n"
        f"Номер заявки: #{request_id}\n"
        f"Ім’я гостя: {context.user_data['guest_guestname']}\n"
        f"Дата входу: {context.user_data['guest_date']}\n\n"
        f"Заявник:\n"
        f"👤 Ім’я: {context.user_data['guest_name']}\n"
        f"🏠 Квартира: {context.user_data['guest_flat']}\n"
        f"📱 Телефон: {context.user_data.get('guest_phone', 'не надано')}\n"
        f"💬 Telegram: {username}"
    )

    keyboard = [[InlineKeyboardButton("📤 Створити ще одну заявку", callback_data="new_request")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_id = query_or_update.message.chat_id if hasattr(query_or_update, "message") else query_or_update.from_user.id
    await context.bot.send_message(chat_id=chat_id, text="✅ Дані збережено та передано охороні.\n\n" + summary, reply_markup=reply_markup)

    # кнопка для охоронця з ID заявника
    keyboard_security = [[InlineKeyboardButton("✅ Прийнято", callback_data=f"accepted_{requester_id}")]]
    reply_markup_security = InlineKeyboardMarkup(keyboard_security)
    await context.bot.send_message(chat_id=SECURITY_CHAT_ID, text=summary, reply_markup=reply_markup_security)

    save_to_log(summary)
    return MENU
# --- Тимчасова команда для отримання chat_id ---
async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш chat_id: {update.message.chat_id}")

# --- Обробка кнопки "Прийнято" від охоронця ---
async def accepted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("accepted_"):
        user_id = int(data.split("_")[1])
        print("✅ accepted callback triggered:", data)   # лог у консоль
        print("📨 sending to user_id:", user_id)        # перевірка ID

        # повідомлення заявнику
        await context.bot.send_message(chat_id=user_id, text="✅ Ваша заявка прийнята охоронцем.")
        # прибираємо кнопку у охоронця
        await query.edit_message_reply_markup(reply_markup=None)

def main():
    app = Application.builder().token("8184081641:AAFIZE2A8CQkw5Gzt-J-ZrTBlAwbzWR2qx4").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(menu_choice)],
            CHOOSING: [CallbackQueryHandler(choose)],

            AUTO_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, auto_name)],
            AUTO_FLAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, auto_flat)],
            AUTO_CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, auto_car)],
            AUTO_PHONE: [MessageHandler(filters.CONTACT, auto_phone)],
            AUTO_DATE: [CallbackQueryHandler(auto_date_choice)],

            GUEST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, guest_name)],
            GUEST_FLAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, guest_flat)],
            GUEST_GUESTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, guest_guestname)],
            GUEST_PHONE: [MessageHandler(filters.CONTACT, guest_phone)],
            GUEST_DATE: [CallbackQueryHandler(guest_date_choice)],
        },
        fallbacks=[],
        per_message=False  # щоб прибрати попередження PTBUserWarning
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("id", show_id))  # тимчасова команда /id
    app.add_handler(CallbackQueryHandler(accepted, pattern="^accepted_"))  # кнопка "Прийнято"

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()