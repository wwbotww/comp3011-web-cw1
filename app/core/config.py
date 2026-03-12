from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Leeds Bus Reliability and Delay Analytics API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./leeds_bus_api.db"
    write_api_key: str = "change-me"
    bods_api_key: str = ""
    data_root: Path = Path("data")
    bods_max_datasets: int = 1
    bods_max_xml_files_per_dataset: int = 8
    bods_preferred_locality: str = "Leeds"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
