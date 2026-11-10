"""FastAPI-приложение для работы с задачами в базе данных."""

import os
from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import (
    DEFAULT_DATABASE_URL,
    Task,
    create_database_engine,
    create_session_factory,
    initialize_database,
)


class TaskCreate(BaseModel):
    """Данные для создания задачи."""

    title: str = Field(min_length=1, max_length=200)


class TaskUpdate(BaseModel):
    """Поля задачи, которые можно изменить."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    completed: Optional[bool] = None


class TaskResponse(BaseModel):
    """Задача в ответе API."""

    id: int
    title: str
    completed: bool


def normalize_title(title: str) -> str:
    """Удаляет лишние пробелы и проверяет название задачи."""
    normalized_title = title.strip()
    if not normalized_title:
        raise ValueError("Название задачи не должно быть пустым")
    return normalized_title


def task_to_response(task: Task) -> TaskResponse:
    """Преобразует модель SQLAlchemy в ответ API."""
    return TaskResponse(
        id=task.id,
        title=task.title,
        completed=task.completed,
    )


def create_app(database_url: str = DEFAULT_DATABASE_URL) -> FastAPI:
    """Создаёт FastAPI-приложение и подключает его к базе данных."""
    engine = create_database_engine(database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    application = FastAPI(
        title="API списка задач",
        description="Создание, просмотр, изменение и удаление задач",
        version="1.0",
    )
    application.state.database_engine = engine
    application.state.session_factory = session_factory

    def get_session() -> Generator[Session, None, None]:
        """Выдаёт отдельную сессию базы данных на время запроса."""
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def get_task_or_404(task_id: int, session: Session) -> Task:
        """Возвращает задачу или отвечает ошибкой 404."""
        task = session.get(Task, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return task

    @application.get("/tasks", response_model=List[TaskResponse])
    def list_tasks(session: Session = Depends(get_session)) -> List[TaskResponse]:
        """Возвращает все задачи по порядку их создания."""
        tasks = session.scalars(select(Task).order_by(Task.id)).all()
        return [task_to_response(task) for task in tasks]

    @application.post(
        "/tasks",
        response_model=TaskResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_task(
        payload: TaskCreate,
        session: Session = Depends(get_session),
    ) -> TaskResponse:
        """Создаёт новую задачу."""
        try:
            title = normalize_title(payload.title)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        task = Task(title=title, completed=False)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task_to_response(task)

    @application.get("/tasks/{task_id}", response_model=TaskResponse)
    def get_task(
        task_id: int,
        session: Session = Depends(get_session),
    ) -> TaskResponse:
        """Возвращает одну задачу по идентификатору."""
        return task_to_response(get_task_or_404(task_id, session))

    @application.patch("/tasks/{task_id}", response_model=TaskResponse)
    def update_task(
        task_id: int,
        payload: TaskUpdate,
        session: Session = Depends(get_session),
    ) -> TaskResponse:
        """Изменяет название или состояние задачи."""
        task = get_task_or_404(task_id, session)
        if payload.title is not None:
            try:
                task.title = normalize_title(payload.title)
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        if payload.completed is not None:
            task.completed = payload.completed

        session.commit()
        session.refresh(task)
        return task_to_response(task)

    @application.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_task(
        task_id: int,
        session: Session = Depends(get_session),
    ) -> Response:
        """Удаляет задачу."""
        task = get_task_or_404(task_id, session)
        session.delete(task)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return application


app = create_app(os.getenv("LAB6_DATABASE_URL", DEFAULT_DATABASE_URL))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_database:app", host="127.0.0.1", port=8001, reload=False)
