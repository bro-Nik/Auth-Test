import os


class Settings:
    ASYNC_DB_URL: str = os.getenv("DB_URL", '')


settings = Settings()
