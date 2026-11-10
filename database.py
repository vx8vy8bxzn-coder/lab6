"""Подключение SQLAlchemy и модель задачи для SQLite."""

from sqlalchemy import Boolean, Column, Integer, String, create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


DEFAULT_DATABASE_URL = "sqlite:///./tasks.db"
Base = declarative_base()


class Task(Base):
    """Задача, которая хранится в базе данных."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    completed = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        """Возвращает понятное представление задачи."""
        return (
            f"Task(id={self.id!r}, title={self.title!r}, completed={self.completed!r})"
        )


def create_database_engine(database_url: str = DEFAULT_DATABASE_URL) -> Engine:
    """Создаёт SQLAlchemy engine для указанной базы данных."""
    if not isinstance(database_url, str) or not database_url.strip():
        raise ValueError("Адрес базы данных не должен быть пустым")

    options = {}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        options["poolclass"] = StaticPool

    return create_engine(database_url, **options)


def create_session_factory(engine: Engine) -> sessionmaker:
    """Создаёт фабрику сессий для переданного engine."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def initialize_database(engine: Engine) -> None:
    """Создаёт таблицы, если их ещё нет."""
    Base.metadata.create_all(bind=engine)


def count_tasks(engine: Engine) -> int:
    """Возвращает количество задач в базе данных."""
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        return int(session.scalar(select(func.count(Task.id))) or 0)


def main() -> None:
    """Создаёт локальную базу и выводит результат подключения."""
    engine = create_database_engine()
    initialize_database(engine)
    print(f"База данных подключена. Задач: {count_tasks(engine)}")
    engine.dispose()


if __name__ == "__main__":
    main()
