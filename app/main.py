from fastapi import FastAPI


app = FastAPI(
    title="Auth Test",
    description="Authentication and Authorization System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/")
async def root():
    return {"message": "Authentication and Authorization System"}
