import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Установите уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Функция для получения информации о диапазонах длин волн
def get_wavelength_info():
    return (
        "Информация о диапазонах длин волн:\n"
        "- Ультрафиолет: 10 нм - 400 нм\n"
        "- Видимый свет: 400 нм - 700 нм\n"
        "- Инфракрасный: 700 нм - 1 мм\n"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_main_menu(update)

async def show_main_menu(update: Update) -> None:
    keyboard = [
        [InlineKeyboardButton("Конвертация", callback_data='convert')],
        [InlineKeyboardButton("Анализ спектра", callback_data='analyze')],
        [InlineKeyboardButton("Флюенс лазера", callback_data='fluence')],
        [InlineKeyboardButton("Информация о диапазонах длин волн", callback_data='wavelength_info')],
        [InlineKeyboardButton("Оставить отзыв", callback_data='feedback')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите, что хотите сделать:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'convert':
        keyboard = [
            [InlineKeyboardButton("Частота в длину волну", callback_data='convert_frequency')],
            [InlineKeyboardButton("Энергия в частоту", callback_data='convert_energy')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите тип конвертации:",
            reply_markup=reply_markup
        )
    elif query.data == 'convert_frequency':
        await query.edit_message_text("Введите частоту (например, '5e14'). Пожалуйста, напишите в чате.")
        context.user_data['conversion_type'] = 'frequency'
    elif query.data == 'convert_energy':
        await query.edit_message_text("Введите энергию (например, '3e-19'). Пожалуйста, напишите в чате.")
        context.user_data['conversion_type'] = 'energy'
    elif query.data == 'analyze':
        await query.edit_message_text("Пожалуйста, загрузите файл с данными спектра в формате .txt.")
    elif query.data == 'fluence':
        await query.edit_message_text("Введите среднюю мощность и площадь (например, '10 0.01').")
        context.user_data['waiting_for_fluence'] = True  # Устанавливаем флаг ожидания флюенса
    elif query.data == 'feedback':
        await query.edit_message_text("Как вы оцениваете использование ассистента от 1 до 5?")
        context.user_data['waiting_for_feedback'] = True  # Устанавливаем флаг ожидания отзыва
    elif query.data == 'wavelength_info':
        info = get_wavelength_info()
        await query.edit_message_text(info)  # Отправляем информацию о диапазонах
        await show_main_menu(query)  # Выводим меню сразу после информации

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user_data = context.user_data

    # Обработка конвертации частоты и энергии
    if user_data.get('conversion_type') == 'frequency':
        try:
            frequency = float(text)
            wavelength = 3e8 / frequency  # Пример расчета длины волны
            await update.message.reply_text(f"Длина волны: {wavelength:.2e} м")
            await show_main_menu(update)  # Показываем меню после результата
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение частоты.")
    elif user_data.get('conversion_type') == 'energy':
        try:
            energy = float(text)
            frequency = energy / (6.626e-34)  # Пример расчета частоты
            await update.message.reply_text(f"Частота: {frequency:.2e} Гц")
            await show_main_menu(update)  # Показываем меню после результата
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение энергии.")

    # Обработка флюенса
    if user_data.get('waiting_for_fluence'):
        try:
            power, area = map(float, text.split())
            fluence = power / area  # Пример расчета флюенса
            await update.message.reply_text(f"Флюенс: {fluence:.2e} Дж/м²")
            user_data['waiting_for_fluence'] = False  # Сбрасываем флаг
            await show_main_menu(update)  # Показываем меню после результата
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректные значения мощности и площади.")

    # Обработка отзыва
    if user_data.get('waiting_for_feedback'):
        try:
            rating = int(text)
            if 1 <= rating <= 5:
                with open("feedback.txt", "a") as f:
                    f.write(f"Оценка: {rating}\n")
                await update.message.reply_text("Спасибо за ваш отзыв!")
                user_data['waiting_for_feedback'] = False  # Сбрасываем флаг
                await show_main_menu(update)  # Показываем меню после отзыва
            else:
                await update.message.reply_text("Пожалуйста, введите число от 1 до 5.")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное значение от 1 до 5.")

def main() -> None:
    application = ApplicationBuilder().token("7877252817:AAFI_4TFACQfEpu0VmKGb24ssapvzLCywJY").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
