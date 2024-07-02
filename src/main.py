import requests
from sqlalchemy.orm import Session
from models import Vacancy, SessionLocal


def get_vacancies(search_text, area=1, page=0, per_page=20):
    """
    Функция для получения вакансий с hh.ru по заданным параметрам.

    :param search_text: текст для поиска вакансий
    :param area: код региона (1 - Москва, 2 - Санкт-Петербург и т.д.)
    :param page: номер страницы (начиная с 0)
    :param per_page: количество вакансий на странице (максимум 100)
    :return: список вакансий
    """
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": search_text,
        "area": area,
        "page": page,
        "per_page": per_page
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def save_vacancies_to_db(vacancies, db_session):
    """
    Функция для сохранения данных о вакансиях в базу данных.

    :param vacancies: список вакансий
    :param db_session: сессия базы данных
    """
    for vacancy in vacancies:
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
    db_session.commit()
