from fastapi import FastAPI

from app.api import auth, user, order, product
from app.temp_db_init import init_tables


app = FastAPI(
    title="Auth Test",
    description="Authentication and Authorization System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(product.router)
app.include_router(order.router)


# ToDo работа с таблицами (временно)
@app.on_event("startup")
async def startup_event():
    await init_tables()


@app.get("/")
async def root():
    return {"message": "Authentication and Authorization System"}
