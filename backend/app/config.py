from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_host: str = Field("0.0.0.0", description="FastAPI bind host")
    api_port: int = Field(8000, description="FastAPI bind port")
    neo4j_uri: str = Field("bolt://neo4j:7687", description="Neo4j bolt URI")
    neo4j_user: str = Field("neo4j", description="Neo4j username")
    neo4j_password: str = Field("neo4jpassword", description="Neo4j password")
    neo4j_database: str | None = Field(None, description="Optional database name")
    request_timeout: float = Field(10.0, description="Neo4j request timeout seconds")
    enable_api_key: bool = Field(False, description="Require API key header if true")
    api_key: str | None = Field(None, description="Static API key in simple deployments")
    storage_dir: str = Field("storage", description="Base directory for local storage")
    kubeconfig_dir: str = Field(
        "storage/kubeconfigs", description="Directory for uploaded kubeconfigs"
    )
    ingestion_job_retention_hours: int = Field(
        24, description="How long to retain ingestion job records"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.kubeconfig_dir).mkdir(parents=True, exist_ok=True)
    return settings
