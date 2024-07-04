import aiohttp
import requests
from sqlalchemy.orm import Session
from models import Vacancy


async def get_vacancies(query: str, city: str, pages: int = 1):
    base_url = "https://api.hh.ru/vacancies"
    vacancies = []

    # Получение города по ID
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.hh.ru/suggests/areas?text={city}") as city_response:
            city_data = await city_response.json()
            if city_data['items']:
                city_id = city_data['items'][0]['id']
            else:
                raise ValueError(f"Город {city} не найден")

    params = {
        "text": query,
        "area": city_id,
        "per_page": 100
    }

    async with aiohttp.ClientSession() as session:
        for page in range(pages):
            params['page'] = page
            async with session.get(base_url, params=params) as response:
                result = await response.json()
                vacancies.extend(result['items'])

                if result['pages'] <= page:
                    break

    return vacancies


def save_vacancies_to_db(vacancies, db_session):
    """
    Функция для сохранения данных о вакансиях в базу данных.

    :param vacancies: список вакансий
    :param db_session: сессия базы данных
    """
    existing_vacancies = db_session.query(Vacancy.url).all()
    existing_urls = {url[0] for url in existing_vacancies}

    for vacancy in vacancies:
        if vacancy['alternate_url'] not in existing_urls:
            salary = vacancy.get('salary')
            salary_from = salary.get('from') if salary else None
            salary_to = salary.get('to') if salary else None
            currency = salary.get('currency') if salary else None

            db_vacancy = Vacancy(
                name=vacancy.get('name'),
                employer=vacancy.get('employer', {}).get('name'),
                salary_from=salary_from,
                salary_to=salary_to,
                currency=currency,
                url=vacancy.get('alternate_url')
            )
            db_session.add(db_vacancy)
        else:
            existing_vacancy = db_session.query(Vacancy).filter(Vacancy.url == vacancy['alternate_url']).first()
            if existing_vacancy:
                existing_vacancy.status = 'не актуально'

    db_session.commit()
