from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import auth, user, order, product, permission
from app.temp_db_init import init_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_tables()
    yield


app = FastAPI(
    title="Auth Test",
    description="Authentication and Authorization System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(permission.router)


@app.get("/")
async def root():
    return {"message": "Authentication and Authorization System"}
