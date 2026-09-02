from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "mysql+pymysql://mess:mess_dev@127.0.0.1:3306/mess_db_test?charset=utf8mb4"
    )
    jwt_secret: str = "change-me-in-dev"
    jwt_access_min: int = 60
    cors_origins: str = "http://localhost:3000"
    seed_staff_password: str = "ChangeMe!"

    # ZKTeco demo pull (no DB). Off → 404 on /api/v1/zk/demo/*
    zk_demo_enabled: bool = True
    # Allow pull without JWT (localStorage demo FE). Turn off in shared/prod.
    zk_demo_anonymous: bool = True
    zk_host: str = "27.147.222.15"
    zk_port: int = 4370
    zk_timeout: int = 10
    zk_password: int = 0


settings = Settings()
