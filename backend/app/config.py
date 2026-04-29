"""Application configuration via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    allowed_hosts: str = "private.pravdalist.ai,api.pravdalist.ai,localhost,127.0.0.1"
    trust_proxy: bool = False
    forwarded_header: str = "x-forwarded-for"
    trusted_proxy_ips: str = ""  # comma-separated list of trusted proxy IPs
    require_real_client_ip: bool = False

    database_url: str = "postgresql+asyncpg://pravdalist:pravdalist@localhost:5432/pravdalist"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 30
    jwt_refresh_ttl_days: int = 14

    ip_block_threshold: int = 5
    ip_block_window_minutes: int = 10
    ip_ban_minutes: int = 60

    default_lang: str = "ua"
    supported_langs: str = "ua,en,ru,de"

    @property
    def allowed_hosts_list(self) -> List[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @property
    def supported_langs_list(self) -> List[str]:
        return [lang.strip() for lang in self.supported_langs.split(",") if lang.strip()]

    @property
    def trusted_proxy_ips_list(self) -> List[str]:
        return [ip.strip() for ip in self.trusted_proxy_ips.split(",") if ip.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
