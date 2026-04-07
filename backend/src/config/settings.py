"""Application settings via Pydantic."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_mode: str = "memory"
    database_url: str = "postgresql+asyncpg://localhost:5432/app"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
