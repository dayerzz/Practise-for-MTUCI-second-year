import requests
from sqlalchemy.orm import Session
from models import Vacancy


def get_vacancies(search_text, area=1, pages=5, per_page=20):
    """
    Функция для получения вакансий с hh.ru по заданным параметрам.

    :param search_text: текст для поиска вакансий
    :param area: код региона (1 - Москва, 2 - Санкт-Петербург и т.д.)
    :param pages: количество страниц для парсинга
    :param per_page: количество вакансий на странице (максимум 100)
    :return: список всех вакансий со всех страниц
    """
    url = "https://api.hh.ru/vacancies"
    all_vacancies = []

    for page in range(pages):
        params = {
            "text": search_text,
            "area": area,
            "page": page,
            "per_page": per_page
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            all_vacancies.extend(data.get('items', []))
        else:
            print(f"Ошибка: {response.status_code}")
            break

    return all_vacancies


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
