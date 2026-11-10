"""Простое Flask-приложение «Hello World»."""

from flask import Flask


def create_app() -> Flask:
    """Создаёт Flask-приложение с приветственным маршрутом."""
    application = Flask(__name__)

    @application.get("/")
    def hello() -> str:
        """Возвращает приветствие на главной странице."""
        return "Привет, Flask!"

    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=False)
