"""Flask-приложение с шаблоном Jinja2 и данными."""

from typing import Dict, Tuple, Union

from flask import Flask, render_template


BookData = Dict[str, Union[str, int]]
BOOKS: Tuple[BookData, ...] = (
    {"title": "Мастер и Маргарита", "author": "Михаил Булгаков", "year": 1967},
    {"title": "Евгений Онегин", "author": "Александр Пушкин", "year": 1833},
    {"title": "Война и мир", "author": "Лев Толстой", "year": 1869},
    {
        "title": "Преступление и наказание",
        "author": "Фёдор Достоевский",
        "year": 1866,
    },
)


def create_app() -> Flask:
    """Создаёт приложение со страницей книжной таблицы."""
    application = Flask(__name__)

    @application.get("/")
    def books_page() -> str:
        """Передаёт список книг в шаблон Jinja2."""
        return render_template(
            "books.html",
            page_title="Моя библиотека",
            books=BOOKS,
        )

    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=False, port=5001)
