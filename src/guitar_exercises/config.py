from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PACKAGE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GUITAR_", env_file=".env", extra="ignore")

    debug: bool = Field(default=False)
    package_dir: Path = Field(default=_PACKAGE_DIR)

    @property
    def templates_dir(self) -> Path:
        return self.package_dir / "templates"

    @property
    def static_dir(self) -> Path:
        return self.package_dir / "static"


def get_settings() -> Settings:
    return Settings()
