from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SalesOps API"
    database_url: str = "postgresql+psycopg://salesops:salesops@postgres:5432/salesops"
    redis_url: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
