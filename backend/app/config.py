# backend/app/config.py


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "LeaseBuddy API"
    ENVIRONMENT: str = "development"
    API_SECRET_KEY: str = "change_me_in_prod"

    # Server Settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Database Settings
    DATABASE_URL: str
    REDIS_URL: str

    # AI Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:8b"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    VECTOR_DIMENSION: int = 768  # nomic-embed-text outputs 768-dimensional vectors

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

settings = Settings()