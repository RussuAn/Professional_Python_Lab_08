# Система обліку студентів

Лабораторна робота №8 «Мережеве та асинхронне програмування. REST API»  
Курс «Професійний Python», варіант №1  
Руссу Анастасія Сергіївна, ФЕП-32  
Викладач: Свелеба С. А.

## Опис роботи

Продовження проєкту Lab_01 і Lab_07: розроблено REST API для системи обліку студентів на FastAPI. Дані про студентів та групи зберігаються в SQLite за допомогою SQLAlchemy. Запити перевіряються Pydantic. Реалізовано GET, POST, PATCH, DELETE, фільтрацію за прізвищем, групою й мінімальним балом, переведення студентів між групами, визначення найкращого студента й середнього бала групи.

Асинхронна частина використовує `async def`, `await`, `asyncio.create_task`, `asyncio.gather`, `asyncio.Semaphore`, HTTPX `AsyncClient`, обмеження часу та повторні спроби. Тести працюють з окремою тимчасовою SQLite БД та HTTPX ASGITransport, не потребуючи доступу до інтернету.

## Структура проєкту

```text
Lab_08_variant_1/
├── pyproject.toml
├── README.md
├── .gitignore
├── alembic.ini
├── migrations/
├── src/student_manager/
│   ├── __init__.py
│   ├── api.py
│   ├── schemas.py
│   ├── dependencies.py
│   ├── database.py
│   ├── models.py
│   ├── repositories.py
│   ├── services.py
│   ├── external_api.py
│   ├── demo_http.py
│   ├── db_api.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_external_api.py
│   ├── test_repositories.py
│   └── test_migrations.py
├── evidence/
└── report/
    └── Report_lab_08.docx
```

## Запуск у Windows

Команди виконуються в **PowerShell** у папці, де знаходиться `pyproject.toml`.

Створення середовища та встановлення пакета:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Створення структури бази даних за допомогою Alembic:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Запуск REST API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn student_manager.api:app --reload
```

У браузері відкрийте Swagger UI: `http://127.0.0.1:8000/docs` (альтернативно `/redoc`).

## Основні endpoints

| Метод | Шлях | Призначення |
|---|---|---|
| GET | `/health` | Перевірка працездатності |
| POST | `/groups` | Створення групи |
| GET | `/groups` | Список груп |
| GET | `/students` | Список/фільтри `group_id`, `last_name`, `min_grade` |
| GET | `/students/best` | Найкращий студент |
| GET | `/students/{student_id}` | Студент за ID |
| POST | `/students` | Додати студента (201) |
| PATCH | `/students/{student_id}` | Змінити бал, групу або дані |
| DELETE | `/students/{student_id}` | Видалити студента (204) |
| GET | `/groups/{group_id}/students` | Студенти групи |
| GET | `/groups/{group_id}/statistics` | Кількість, середній бал, найкращий студент |

## Приклад JSON

```json
{"first_name":"Марія","last_name":"Дорош","group_id":1,"average_grade":86.5}
```

Некоректні дані повертають `422`, відсутня група або студент — `404`, конфлікт унікальності — `409`.

## Тести та HTTPX

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m pytest --cov=student_manager --cov-report=term-missing
.\.venv\Scripts\python.exe -m student_manager.demo_http
```

## Асинхронна обробка

`external_api.fetch_group_statistics()` створює `asyncio.Task` для кожної групи, збирає результати через `gather`, використовує `Semaphore` для обмеження одночасних запитів і `fetch_with_retry()` із timeout, backoff і повторними спробами. Для відтворюваних тестів зовнішній HTTP-сервіс моделюється `httpx.MockTransport` і `httpx.ASGITransport`.

## Обробка даних

Середній бал зберігається у межах 0–100. Імена не можуть бути порожніми. Пошук за прізвищем не враховує регістр, зокрема українські літери. Для групи без студентів середній бал і найкращий студент повертаються як `null`. База даних зберігає дані між запусками, окрім ізольованих тестів.

## Git

Перевірка локальної історії:

```powershell
git status
git log --oneline
```
