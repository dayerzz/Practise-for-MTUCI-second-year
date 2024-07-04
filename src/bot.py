import asyncio
import logging
from telegram import Update
from telegram.ext import (Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackContext)
from models import Vacancy, SessionLocal
from main import get_vacancies, save_vacancies_to_db, search_db_vacancies
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

ASKING_CITY, ASKING_VACANCY, ASKING_SKILLS, ASKING_SALARY_FROM, ASKING_SALARY_TO, ASKING_WORK_FORMAT = range(6)
user_query = {}


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет! Я бот-парсер для поиска вакансий. Используйте команду /search, чтобы найти вакансии.'
    )


async def search(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('В каком городе вы ищете работу?')
    return ASKING_CITY


async def city(update: Update, context: CallbackContext) -> int:
    user_query['city'] = update.message.text
    await update.message.reply_text('Какую вакансию вы хотите найти?')
    return ASKING_VACANCY


async def title(update: Update, context: CallbackContext) -> int:
    user_query['title'] = update.message.text
    await update.message.reply_text('Какие навыки вы имеете? Если хотите пропустить этот шаг, напишите ">".')
    return ASKING_SKILLS


async def skills(update: Update, context: CallbackContext) -> int:
    skills = update.message.text
    if skills != '>':
        user_query['skills'] = [skill.strip().lower() for skill in skills.split(',')]
    else:
        user_query['skills'] = []

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

    query = f"{user_query.get('title', '')}".strip()
    # skills = ', '.join(user_query.get('skills', []))
    city = user_query.get("city", "")
    await update.message.reply_text(f'Ищу вакансии для запроса: {query} в городе {city}')

    # Получение данных
    max_pages = 1
    try:
        all_vacancies = await asyncio.wait_for(get_vacancies(query, city, pages=max_pages), timeout=360.0)
    except asyncio.TimeoutError:
        await update.message.reply_text('Время ожидания запроса истекло. Попробуйте снова.')
        return ConversationHandler.END

    db_session = SessionLocal()

    db_vacancies = search_db_vacancies(
        user_query['title'],
        user_query['city'],
        user_query['skills'],
        user_query['salary_from'],
        user_query['salary_to'],
        db_session
    )

    filtered_vacancies = []
    for vac in all_vacancies + db_vacancies:
        if isinstance(vac, dict):
            salary = vac.get('salary')
            if salary:
                vac_salary_from = salary.get('from') or 0
                vac_salary_to = salary.get('to') or float('inf')
                if (user_query['salary_from'] is not None and vac_salary_from < user_query['salary_from']) or \
                        (user_query['salary_to'] is not None and vac_salary_to > user_query['salary_to']):
                    continue

            if user_query['skills']:
                description = vac.get('description', '').lower() if vac.get('description') else ""
                requirements = vac.get('snippet', {}).get('requirement', '').lower() if vac.get(
                    'snippet') and vac.get('snippet').get('requirement') else ""
                if not any(skill in description or skill in requirements for skill in user_query['skills']):
                    continue

            filtered_vacancies.append(vac)
        else:
            filtered_vacancies.append(vac)

    save_vacancies_to_db(filtered_vacancies, db_session)

    response_texts = []
    for vac in filtered_vacancies:
        if isinstance(vac, dict):
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
        else:
            salary_from = vac.salary_from
            salary_to = vac.salary_to
            currency = vac.currency
            salary_str = f"{salary_from} - {salary_to} {currency}" if salary_from and salary_to else \
                f"{salary_from} {currency}" if salary_from else \
                    f"{salary_to} {currency}" if salary_to else "Зарплата не указана"

            response_text = f"{vac.name} - {vac.employer}\n{salary_str}\n{vac.url}"
            response_texts.append(response_text)

    count_message = f"Найдено {len(filtered_vacancies)} вакансий\n\n"
    await update.message.reply_text(count_message)

    batch_size = 20
    current_batch = []

    for i, response in enumerate(response_texts):
        current_batch.append(response)
        if (i + 1) % batch_size == 0 or i == len(response_texts) - 1:
            batch_message = "\n\n".join(current_batch)
            if len(batch_message) > 4096:
                for j in range(0, len(batch_message), 4096):
                    await update.message.reply_text(batch_message[j:j + 4096])
            else:
                await update.message.reply_text(batch_message)
            current_batch = []

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
            ASKING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            ASKING_VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
            ASKING_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, skills)],
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
