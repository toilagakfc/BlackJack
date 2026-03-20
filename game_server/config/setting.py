from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ---------- APP ----------
    app_name: str = "game_server"
    app_port: int = 8000
    environment: str = "dev"

    # ---------- MONGO ----------
    # Set MONGO_URI_OVERRIDE in .env to use Atlas (or any full URI).
    # Leave blank to fall back to the host/port/user/password fields (local).
    ROOM_STORAGE: str = "memory"
    mongo_uri_override: str = ""
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_db: str = "blackjack"
    mongo_user: str = "admin"
    mongo_password: str = "mongo123"

    # ---------- REDIS ----------
    GAME_STORAGE: str = "mongo"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # ---------- SOCKET ----------
    socket_cors: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # ---------- computed fields ----------

    @property
    def mongo_uri(self) -> str:
        # Atlas (or any full URI) supplied via env takes priority
        if self.mongo_uri_override:
            return self.mongo_uri_override
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/?authSource=admin"
        )

    @property
    def redis_uri(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()