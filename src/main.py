import aiohttp
from models import Vacancy
from sqlalchemy import or_


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
        "search_field": "name",
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

    db_session.commit()


def search_db_vacancies(query, city, skills, salary_from, salary_to, db_session):
    query = db_session.query(Vacancy)

    if query:
        query = query.filter(Vacancy.name.ilike(f"%{query}%"))

    if city:
        query = query.filter(Vacancy.employer.ilike(f"%{city}%"))

    if skills:
        skill_filters = [Vacancy.description.ilike(f"%{skill}%") for skill in skills]
        query = query.filter(or_(*skill_filters))

    if salary_from:
        query = query.filter(Vacancy.salary_from >= salary_from)

    if salary_to:
        query = query.filter(Vacancy.salary_to <= salary_to)

    return query.all()
