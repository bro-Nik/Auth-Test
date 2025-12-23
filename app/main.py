from app.api import auth
from fastapi import FastAPI

from app.core import database


app = FastAPI(
    title="Auth Test",
    description="Authentication and Authorization System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


app.include_router(auth.router)


# ToDo работа с таблицами (временно)
@app.on_event("startup")
async def startup_event():
    await database.init_tables()


@app.get("/")
async def root():
    return {"message": "Authentication and Authorization System"}
