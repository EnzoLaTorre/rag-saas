from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str = "sqlite:///./rag.db"
    jwt_secret: str
    access_token_expire_minutes: int = 30

    model_config = {"env_file": ".env"}

settings = Settings()