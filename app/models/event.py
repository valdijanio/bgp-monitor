"""
Dataclasses para eventos e logs do sistema.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    """Representa um evento do sistema de monitoramento."""

    event_type: str
    severity: str
    source: str
    message: str
    details: Optional[str] = None
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    @property
    def is_critical(self) -> bool:
        """Verifica se o evento é crítico."""
        return self.severity.lower() == "critical"

    @property
    def is_warning(self) -> bool:
        """Verifica se o evento é um aviso."""
        return self.severity.lower() == "warning"

    @property
    def is_info(self) -> bool:
        """Verifica se o evento é informativo."""
        return self.severity.lower() == "info"

    @property
    def is_bgp_event(self) -> bool:
        """Verifica se é um evento BGP."""
        return self.event_type.lower().startswith("bgp_")

    @property
    def is_interface_event(self) -> bool:
        """Verifica se é um evento de interface."""
        return self.event_type.lower().startswith("interface_")

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "is_critical": self.is_critical,
            "is_warning": self.is_warning,
            "is_info": self.is_info,
            "is_bgp_event": self.is_bgp_event,
            "is_interface_event": self.is_interface_event,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class SSHCommandLog:
    """Representa o log de um comando SSH executado."""

    command: str
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    @property
    def execution_time_seconds(self) -> float:
        """Retorna o tempo de execução em segundos."""
        return self.execution_time_ms / 1000

    @property
    def has_error(self) -> bool:
        """Verifica se houve erro."""
        return not self.success or self.error_message is not None

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "command": self.command,
            "execution_time_ms": self.execution_time_ms,
            "execution_time_seconds": round(self.execution_time_seconds, 3),
            "success": self.success,
            "error_message": self.error_message,
            "has_error": self.has_error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
