from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_user: str = Field(validation_alias="POSTGRES_USER")
    postgres_password: str = Field(validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(validation_alias="POSTGRES_DB")
    postgres_host: str = Field(validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(validation_alias="POSTGRES_PORT")

    rabbitmq_default_user: str = Field(validation_alias="RABBITMQ_DEFAULT_USER")
    rabbitmq_default_pass: str = Field(validation_alias="RABBITMQ_DEFAULT_PASS")

    minio_root_user: str = Field(validation_alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(validation_alias="MINIO_ROOT_PASSWORD")
    minio_endpoint: str = Field(validation_alias="MINIO_ENDPOINT")
    minio_secure: bool = Field(
        default=False,
        validation_alias="MINIO_SECURE",
    )

    redis_host: str = Field(validation_alias="REDIS_HOST")
    redis_port: int = Field(
        default=6379,
        validation_alias="REDIS_PORT",
    )

    celery_broker_url: str = Field(validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(validation_alias="CELERY_RESULT_BACKEND")

    api_keys_raw: str = Field(validation_alias="API_KEYS")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def get_api_keys(self) -> list[str]:
        return [k.strip() for k in self.api_keys_raw.split(",")]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def minio_url(self) -> str:
        protocol = "https" if self.minio_secure else "http"
        return f"{protocol}://{self.minio_endpoint}"

settings = Settings()