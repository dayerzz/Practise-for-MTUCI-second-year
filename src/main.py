import aiohttp
from models import Vacancy
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Union


async def get_vacancies(query: str, city: str, pages: int) -> List[Dict[str, Union[str, int, Dict[str, Union[int, str]]]]]:
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
        "search_field": "name",
        "per_page": 100
    }

    async with aiohttp.ClientSession() as session:
        for page in range(pages):
            params['page'] = page
            async with session.get(base_url, params=params) as response:
                result = await response.json()
                for item in result['items']:
                    salary = item.get('salary', {})
                    salary_from = salary.get('from') if salary else None
                    salary_to = salary.get('to') if salary else None
                    currency = salary.get('currency') if salary else None

                    vacancy = Vacancy(
                        name=item.get('name'),
                        employer=item.get('employer', {}).get('name'),
                        salary_from=salary_from,
                        salary_to=salary_to,
                        currency=currency,
                        url=item.get('alternate_url'),
                        city=city,
                        skills=item.get('snippet', {}).get('requirement')
                    )
                    vacancies.append(vacancy)

                if result['pages'] <= page:
                    break

    return vacancies


def save_vacancies_to_db(vacancies: List[Dict[str, Union[str, int, Dict[str, Union[int, str]]]]], db_session: Session) -> None:
    existing_vacancies = db_session.query(Vacancy.url).all()
    existing_urls = {url[0] for url in existing_vacancies}

    for vacancy in vacancies:
        if vacancy.url not in existing_urls:
            db_session.add(vacancy)

    db_session.commit()


def search_db_vacancies(query: str, city: str, skills: List[str], salary_from: int, salary_to: int, db_session: Session) -> List[Vacancy]:
    db_query = db_session.query(Vacancy)

    if query:
        db_query = db_query.filter(Vacancy.name.ilike(f"%{query}%"))

    if city:
        db_query = db_query.filter(Vacancy.city.ilike(f"%{city}%"))

    if skills:
        skill_filters = [Vacancy.skills.ilike(f"%{skill}%") for skill in skills]
        db_query = db_query.filter(or_(*skill_filters))

    if salary_from:
        db_query = db_query.filter(Vacancy.salary_from >= salary_from)

    if salary_to:
        db_query = db_query.filter(Vacancy.salary_to <= salary_to)

    return db_query.all()
