import os


class Settings:
    ASYNC_DB_URL: str = os.getenv("DB_URL", '')

    JWT_SECRET: str = os.getenv("JWT_SECRET", '')
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", '')
    ACCESS_TOKEN_EXPIRE_MINUTES = 30


settings = Settings()
