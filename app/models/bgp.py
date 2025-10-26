"""
Dataclasses para sessões BGP.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BGPSession:
    """Representa uma sessão BGP com um peer."""

    peer_ip: str
    peer_asn: str
    status: str
    peer_description: Optional[str] = None
    uptime_seconds: int = 0
    prefixes_received: int = 0
    prefixes_sent: int = 0
    last_state_change: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    @property
    def is_established(self) -> bool:
        """Verifica se a sessão está estabelecida."""
        return self.status.lower() == "established"

    @property
    def is_down(self) -> bool:
        """Verifica se a sessão está down."""
        return self.status.lower() == "down"

    @property
    def uptime_hours(self) -> float:
        """Retorna o uptime em horas."""
        return self.uptime_seconds / 3600

    @property
    def uptime_days(self) -> float:
        """Retorna o uptime em dias."""
        return self.uptime_seconds / 86400

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "peer_ip": self.peer_ip,
            "peer_asn": self.peer_asn,
            "peer_description": self.peer_description,
            "status": self.status,
            "uptime_seconds": self.uptime_seconds,
            "uptime_hours": round(self.uptime_hours, 2),
            "uptime_days": round(self.uptime_days, 2),
            "prefixes_received": self.prefixes_received,
            "prefixes_sent": self.prefixes_sent,
            "is_established": self.is_established,
            "is_down": self.is_down,
            "last_state_change": (
                self.last_state_change.isoformat() if self.last_state_change else None
            ),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class BGPStatusHistory:
    """Representa um ponto no histórico de status BGP."""

    peer_ip: str
    status: str
    prefixes_received: int = 0
    prefixes_sent: int = 0
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "peer_ip": self.peer_ip,
            "status": self.status,
            "prefixes_received": self.prefixes_received,
            "prefixes_sent": self.prefixes_sent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
