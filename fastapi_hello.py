"""Простое приложение FastAPI с приветственным маршрутом."""

from typing import Dict

from fastapi import FastAPI


app = FastAPI(title="FastAPI Hello", version="1.0")


@app.get("/")
def hello() -> Dict[str, str]:
    """Возвращает приветствие в формате JSON."""
    return {"message": "Привет, FastAPI!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_hello:app", host="127.0.0.1", port=8000, reload=False)
