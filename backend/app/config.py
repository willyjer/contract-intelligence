from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    cohere_api_key: str
    query_rate_limit_per_hour: int = 20
    upload_rate_limit_per_hour: int = 5
    max_user_uploads: int = 50
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env"}


settings = Settings()
