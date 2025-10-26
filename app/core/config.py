"""
Configurações da aplicação carregadas a partir do arquivo .env.

IMPORTANTE: Não pode ter valores padrão - todas as variáveis devem estar no .env
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação BGP Monitor."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Configurações SSH do Huawei NE8000
    SSH_HOST: str
    SSH_PORT: int
    SSH_USER: str
    SSH_PASSWORD: str

    # Configurações do Banco de Dados SQLite
    DB_PATH: str

    # Configurações da API
    API_HOST: str
    API_PORT: int

    # Configurações de Coleta
    COLLECTION_INTERVAL_SECONDS: int

    # Configurações de Alertas
    ALERT_BGP_DOWN_ENABLED: bool
    ALERT_INTERFACE_DOWN_ENABLED: bool
    ALERT_ERROR_THRESHOLD: int


# Instância global de configurações
settings = Settings()
