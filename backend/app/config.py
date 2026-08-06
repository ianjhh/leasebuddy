# backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# BaseSettings automatically reads from our .env file!
class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "LeaseGPT API"
    ENVIRONMENT: str = "development"
    API_SECRET_KEY: str = "change_me_in_prod"

    # Database Settings
    DATABASE_URL: str
    REDIS_URL: str

    # AI Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:8b"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # We define the dimension of our vector based on the model we use.
    # nomic-embed-text outputs a list of 768 numbers.
    VECTOR_DIMENSION: int = 768

    # This tells Pydantic to look for a file named .env in the parent directory
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

# Create a global instance of settings to use throughout our app
settings = Settings()