import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
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


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет! Я бот-парсер для поиска вакансий. Используйте команду /search <запрос>, чтобы найти вакансии.'
    )


async def search(update: Update, context: CallbackContext) -> None:
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text('Пожалуйста, укажите запрос для поиска вакансий.')
        return

    await update.message.reply_text(f'Ищу вакансии для запроса: {query}')

    data = get_vacancies(query)

    if data:
        vacancies = data.get('items', [])

        db_session = SessionLocal()
        save_vacancies_to_db(vacancies, db_session)
        db_session.close()

        response_texts = []
        for vac in vacancies:
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
        await update.message.reply_text(response or 'Нет найденных вакансий.')
    else:
        await update.message.reply_text('Произошла ошибка при получении данных.')


def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))

    application.run_polling()


if __name__ == '__main__':
    main()
