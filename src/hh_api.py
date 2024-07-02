import requests


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


def parse_vacancies(data):
    """
    Функция для парсинга и вывода данных о вакансиях.

    :param data: данные о вакансиях в формате JSON
    """
    if data:
        vacancies = data.get('items', [])

        for vacancy in vacancies:
            name = vacancy.get('name')
            employer = vacancy.get('employer', {}).get('name')
            salary = vacancy.get('salary')
            if salary:
                salary_from = salary.get('from')
                salary_to = salary.get('to')
                currency = salary.get('currency')
                salary_str = f"{salary_from} - {salary_to} {currency}"
            else:
                salary_str = "Не указана"

            print(f"Вакансия: {name}")
            print(f"Работодатель: {employer}")
            print(f"Зарплата: {salary_str}")
            print(f"Ссылка: {vacancy.get('alternate_url')}")
            print("-" * 40)
    else:
        print("Нет данных для отображения.")


if __name__ == "__main__":
    search_text = "Python developer"
    area = 1  # Москва
    page = 0
    per_page = 10

    data = get_vacancies(search_text, area, page, per_page)
    parse_vacancies(data)
