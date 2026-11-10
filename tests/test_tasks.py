"""Проверки всех заданий варианта 9."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import inspect, select

os.environ["LAB6_DATABASE_URL"] = "sqlite://"

from database import (  # noqa: E402
    Task,
    count_tasks,
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from fastapi_database import create_app as create_database_api  # noqa: E402
from fastapi_hello import app as hello_api  # noqa: E402
from flask_hello import create_app as create_flask_hello  # noqa: E402
from flask_jinja import BOOKS, create_app as create_flask_jinja  # noqa: E402


class FlaskHelloTests(unittest.TestCase):
    """Проверки Flask-приложения Hello World."""

    def setUp(self) -> None:
        """Создаёт тестовый клиент Flask."""
        self.client = create_flask_hello().test_client()

    def test_main_page_returns_greeting(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "Привет, Flask!")

    def test_unknown_page_returns_404(self) -> None:
        self.assertEqual(self.client.get("/unknown").status_code, 404)


class FlaskJinjaTests(unittest.TestCase):
    """Проверки страницы с шаблоном Jinja2."""

    def setUp(self) -> None:
        """Создаёт тестовый клиент приложения с шаблоном."""
        self.client = create_flask_jinja().test_client()

    def test_page_contains_title(self) -> None:
        html = self.client.get("/").get_data(as_text=True)

        self.assertIn("Моя библиотека", html)

    def test_page_contains_all_books(self) -> None:
        html = self.client.get("/").get_data(as_text=True)

        for book in BOOKS:
            self.assertIn(str(book["title"]), html)
            self.assertIn(str(book["author"]), html)
            self.assertIn(str(book["year"]), html)

    def test_template_renders_one_row_per_book(self) -> None:
        html = self.client.get("/").get_data(as_text=True)

        self.assertEqual(html.count("<tr>"), len(BOOKS) + 1)

    def test_stylesheet_is_available(self) -> None:
        response = self.client.get("/static/style.css")
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 200)
        self.assertIn(".table-wrapper", response.get_data(as_text=True))


class FastAPIHelloTests(unittest.TestCase):
    """Проверки приветственного приложения FastAPI."""

    def test_main_route_returns_json_greeting(self) -> None:
        with TestClient(hello_api) as client:
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Привет, FastAPI!"})

    def test_swagger_documentation_is_available(self) -> None:
        with TestClient(hello_api) as client:
            response = client.get("/docs")

        self.assertEqual(response.status_code, 200)
        self.assertIn("swagger-ui", response.text)


class DatabaseTests(unittest.TestCase):
    """Проверки подключения и модели SQLAlchemy."""

    def setUp(self) -> None:
        """Создаёт отдельную базу в памяти."""
        self.engine = create_database_engine("sqlite://")
        initialize_database(self.engine)
        self.session_factory = create_session_factory(self.engine)

    def tearDown(self) -> None:
        """Закрывает подключение после теста."""
        self.engine.dispose()

    def test_creates_tasks_table(self) -> None:
        self.assertIn("tasks", inspect(self.engine).get_table_names())

    def test_saves_and_reads_task(self) -> None:
        with self.session_factory() as session:
            session.add(Task(title="Изучить SQLAlchemy", completed=False))
            session.commit()

        with self.session_factory() as session:
            task = session.scalar(select(Task))

        self.assertIsNotNone(task)
        self.assertEqual(task.title, "Изучить SQLAlchemy")
        self.assertFalse(task.completed)

    def test_counts_saved_tasks(self) -> None:
        with self.session_factory() as session:
            session.add_all(
                [
                    Task(title="Первая", completed=False),
                    Task(title="Вторая", completed=True),
                ]
            )
            session.commit()

        self.assertEqual(count_tasks(self.engine), 2)

    def test_task_representation_contains_values(self) -> None:
        task = Task(id=3, title="Проверить базу", completed=True)

        self.assertIn("Проверить базу", repr(task))
        self.assertIn("completed=True", repr(task))

    def test_rejects_empty_database_url(self) -> None:
        with self.assertRaises(ValueError):
            create_database_engine("   ")


class FastAPIDatabaseTests(unittest.TestCase):
    """Проверки CRUD API с отдельной тестовой базой."""

    def setUp(self) -> None:
        """Создаёт временную базу и тестовый HTTP-клиент."""
        self.temporary_directory = TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "tasks.db"
        self.application = create_database_api(f"sqlite:///{database_path}")
        self.client = TestClient(self.application)

    def tearDown(self) -> None:
        """Закрывает клиент и удаляет временную базу."""
        self.client.close()
        self.application.state.database_engine.dispose()
        self.temporary_directory.cleanup()

    def create_task(self, title: str = "Сделать лабораторную") -> dict:
        """Создаёт задачу и возвращает JSON-ответ."""
        response = self.client.post("/tasks", json={"title": title})
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_empty_database_returns_empty_list(self) -> None:
        response = self.client.get("/tasks")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_creates_task_and_trims_title(self) -> None:
        task = self.create_task("  Проверить API  ")

        self.assertEqual(task["title"], "Проверить API")
        self.assertFalse(task["completed"])
        self.assertIsInstance(task["id"], int)

    def test_lists_tasks_in_creation_order(self) -> None:
        first = self.create_task("Первая")
        second = self.create_task("Вторая")

        response = self.client.get("/tasks")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [task["id"] for task in response.json()], [first["id"], second["id"]]
        )

    def test_returns_task_by_id(self) -> None:
        created = self.create_task()

        response = self.client.get(f"/tasks/{created['id']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), created)

    def test_updates_title_and_status(self) -> None:
        created = self.create_task()

        response = self.client.patch(
            f"/tasks/{created['id']}",
            json={"title": "  Готово  ", "completed": True},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Готово")
        self.assertTrue(response.json()["completed"])

    def test_deletes_task(self) -> None:
        created = self.create_task()

        delete_response = self.client.delete(f"/tasks/{created['id']}")
        get_response = self.client.get(f"/tasks/{created['id']}")

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(delete_response.content, b"")
        self.assertEqual(get_response.status_code, 404)

    def test_missing_task_returns_404_for_all_operations(self) -> None:
        self.assertEqual(self.client.get("/tasks/999").status_code, 404)
        self.assertEqual(
            self.client.patch("/tasks/999", json={"completed": True}).status_code,
            404,
        )
        self.assertEqual(self.client.delete("/tasks/999").status_code, 404)

    def test_rejects_empty_title(self) -> None:
        response = self.client.post("/tasks", json={"title": "   "})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["detail"], "Название задачи не должно быть пустым"
        )

    def test_rejects_title_longer_than_limit(self) -> None:
        response = self.client.post("/tasks", json={"title": "а" * 201})

        self.assertEqual(response.status_code, 422)

    def test_openapi_contains_crud_routes(self) -> None:
        schema = self.client.get("/openapi.json").json()

        self.assertIn("/tasks", schema["paths"])
        self.assertIn("/tasks/{task_id}", schema["paths"])


if __name__ == "__main__":
    unittest.main()
