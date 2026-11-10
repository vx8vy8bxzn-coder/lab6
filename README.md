Лукьянова Юлия Владимировна, группа 221341, вариант 9, лабораторная №6

В этой работе я изучала веб-программирование с помощью Flask, FastAPI, Jinja2 и SQLAlchemy.

Задания средней сложности:

- №9 — шаблон Jinja2 с данными о книгах;
- №1 — Flask-приложение «Hello World»;
- №6 — FastAPI-приложение «Hello».

Задания повышенной сложности:

- №9 — подключение SQLAlchemy к SQLite;
- №2 — FastAPI с базой данных и CRUD-операциями для задач.

Структура проекта:

- `flask_hello.py` — простая страница с приветствием;
- `flask_jinja.py`, `templates/` и `static/` — страница библиотеки;
- `fastapi_hello.py` — приветствие в формате JSON;
- `database.py` — модель задачи и подключение SQLAlchemy;
- `fastapi_database.py` — API для работы со списком задач;
- `tests/` — 23 автоматические проверки.

Перед запуском нужно установить зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Примеры запуска из корня репозитория:

```bash
python3 flask_hello.py
python3 flask_jinja.py
python3 fastapi_hello.py
python3 database.py
python3 fastapi_database.py
```

Flask-приложения открываются по адресам `http://127.0.0.1:5000` и `http://127.0.0.1:5001`. Документация FastAPI доступна по адресам `http://127.0.0.1:8000/docs` и `http://127.0.0.1:8001/docs`. Команда `python3 database.py` создаёт локальный файл `tasks.db` и выводит количество сохранённых задач.

В API базы данных доступны следующие запросы:

- `GET /tasks` и `POST /tasks` — список и создание задач;
- `GET /tasks/{id}` — получение одной задачи;
- `PATCH /tasks/{id}` — изменение названия или статуса;
- `DELETE /tasks/{id}` — удаление задачи.

Тесты используют временную SQLite-базу и не меняют рабочие данные. Запуск:

```bash
python3 -m unittest discover -s tests -v
```

