from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    pihole_host: str = "localhost"
    pihole_port: int = 80
    pihole_password: str = ""
    pihole_https: bool = False
    scrape_interval: int = 30
    exporter_port: int = 9666
    log_level: str = "INFO"

    model_config = SettingsConfigDict(extra="ignore")


SETTINGS = Settings()
