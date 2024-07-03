import logging
from telegram import Update
from telegram.ext import (Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackContext)
from models import Vacancy, SessionLocal
from main import get_vacancies, save_vacancies_to_db
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Для логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

ASKING_VACANCY, ASKING_SKILLS, ASKING_SALARY_FROM, ASKING_SALARY_TO, ASKING_WORK_FORMAT = range(5)
user_query = {}


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет! Я бот-парсер для поиска вакансий. Используйте команду /search, чтобы найти вакансии.'
    )


async def search(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Какую вакансию вы хотите найти?')
    return ASKING_VACANCY


async def title(update: Update, context: CallbackContext) -> int:
    user_query['title'] = update.message.text
    await update.message.reply_text('Какие навыки вы имеете? Если хотите пропустить этот шаг, напишите ">".')
    return ASKING_SKILLS


async def skills(update: Update, context: CallbackContext) -> int:
    skills = update.message.text
    user_query['skills'] = skills if skills != '>' else ''
    await update.message.reply_text('Какой формат работы вас интересует? Если хотите пропустить этот шаг, напишите ">".')
    return ASKING_WORK_FORMAT


async def work_format(update: Update, context: CallbackContext) -> int:
    work_format = update.message.text
    user_query['work_format'] = work_format if work_format != '>' else ''
    await update.message.reply_text('Укажите минимальную зарплату (в рублях). Если хотите пропустить этот шаг,'
                                    ' напишите ">".')
    return ASKING_SALARY_FROM


async def salary_from(update: Update, context: CallbackContext) -> int:
    salary_from = update.message.text
    user_query['salary_from'] = int(salary_from) if salary_from != '>' else None
    await update.message.reply_text('Укажите максимальную зарплату (в рублях). Если хотите пропустить этот шаг,'
                                    ' напишите ">".')
    return ASKING_SALARY_TO


async def salary_to(update: Update, context: CallbackContext) -> int:
    salary_to = update.message.text
    user_query['salary_to'] = int(salary_to) if salary_to != '>' else None

    query = f"{user_query.get('title', '')} {user_query.get('skills', '')} {user_query.get('work_format', '')}".strip()
    await update.message.reply_text(f'Ищу вакансии для запроса: {query}')

    # Получение данных
    max_pages = 5
    all_vacancies = get_vacancies(query, pages=max_pages)

    db_session = SessionLocal()

    if all_vacancies:
        # Фильтры
        filtered_vacancies = []
        for vac in all_vacancies:
            if isinstance(vac, dict):
                salary = vac.get('salary')
                if salary:
                    vac_salary_from = salary.get('from') or 0
                    vac_salary_to = salary.get('to') or float('inf')
                    if (user_query['salary_from'] is not None and vac_salary_from < user_query['salary_from']) or \
                            (user_query['salary_to'] is not None and vac_salary_to > user_query['salary_to']):
                        continue
                if user_query['work_format'] and user_query['work_format'].lower() not in vac.get('schedule', {}).get(
                        'name', '').lower():
                    continue
                filtered_vacancies.append(vac)

        save_vacancies_to_db(filtered_vacancies, db_session)

        response_texts = []
        for vac in filtered_vacancies:
            salary = vac.get('salary')
            if salary:
                salary_from = salary.get('from')
                salary_to = salary.get('to')
                currency = salary.get('currency')
                if currency == "RUR":
                    currency = "₽"
                salary_str = f"{salary_from} - {salary_to} {currency}" if salary_from and salary_to else \
                    f"{salary_from} {currency}" if salary_from else \
                        f"{salary_to} {currency}" if salary_to else "Зарплата не указана"
            else:
                salary_str = "Зарплата не указана"

            response_text = f"{vac['name']} - {vac['employer']['name']}\n{salary_str}\n{vac['alternate_url']}"
            response_texts.append(response_text)

        response = '\n\n'.join(response_texts)
        count_message = f"Найдено {len(filtered_vacancies)} вакансий\n\n"
        await update.message.reply_text(count_message + (response or 'Нет найденных вакансий.'))

    else:
        await update.message.reply_text('Произошла ошибка при получении данных.')

    db_session.close()
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Поиск отменен.')
    return ConversationHandler.END


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('search', search)],
        states={
            ASKING_VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
            ASKING_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, skills)],
            ASKING_WORK_FORMAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, work_format)],
            ASKING_SALARY_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_from)],
            ASKING_SALARY_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_to)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))

    application.run_polling()


if __name__ == '__main__':
    main()
