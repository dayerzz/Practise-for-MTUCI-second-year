# Practise-for-MTUCI-second-year
## Описание проекта
Этот проект предназначен для автоматизированного сбора данных о вакансиях с сайта hh.ru.
Он включает в себя парсер, базу данных PostgreSQL и бот для обработки данных.
В данном файле приведены инструкции по установке и запуску проекта с использованием Docker и Docker Compose.
## Требования
* [Git](https://git-scm.com)
* [Docker Desktop](https://www.docker.com/products/docker-desktop/)
## Инструкция по установке и запуску
1. **Клонирование репозитория:**
Сначала склонируйте репозиторий с проектом на свой локальный компьютер. Для этого выполните следующую команду в терминале:
```bash
git clone https://github.com/dayerzz/Practise-for-MTUCI-second-year.git
```
2. **Перейдите в каталог проекта:**
Перейдите в каталог, содержащий файлы проекта:
```bash
cd <НАЗВАНИЕ_КАТАЛОГА>
```
3. **Установка Docker Desktop:**
Убедитесь, что Docker Desktop установлен на вашем компьютере. Если нет, скачайте и установите его с официального сайта [Docker](https://www.docker.com/products/docker-desktop/).
4. **Создайте файл .env:**
Создайте файл .env в корневой папке проекта и добавьте в него следующие переменные окружения:
```bash
BOT_TOKEN=ваш_бот_токен
DATABASE_URL=ваш_урл_базы_данных
POSTGRES_USER=пользователь_postgres
POSTGRES_PASSWORD=пароль_postgres
POSTGRES_DB=имя_базы_данных
```
5. **Сборка и запуск контейнеров:**
Для сборки и запуска контейнеров c ботом и базой данных выполните следующую команду в корневой папке проекта:
```bash
docker-compose up --build
```
6. **Проверка состояния контейнеров:**
Убедитесь, что контейнеры работают корректно. Вы можете проверить состояние контейнеров с помощью команды:
```bash
docker ps
```
7. **Использование проекта:**
После успешного запуска проекта, бот начнет парсинг данных с hh.ru и сохранение их в базу данных PostgreSQL. Вы можете взаимодействовать с ботом для получения и обработки данных.
 **Доступные команды бота:**
*/start - начать диалог с ботом
*/search - начать поиск вакансий
*/help - получить помощь по командам
*/cancel - отменить текущий поиск
8. **Остановка контейнеров:**
Для остановки работы контейнеров выполните следующую команду:
```bash
docker-compose down
```
