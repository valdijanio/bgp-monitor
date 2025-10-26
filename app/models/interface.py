"""
Dataclasses para interfaces de rede.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Interface:
    """Representa uma interface de rede do NE8000."""

    name: str
    status: str
    description: Optional[str] = None
    bandwidth_capacity: int = 0
    bandwidth_in_bps: int = 0
    bandwidth_out_bps: int = 0
    packets_in_pps: int = 0
    packets_out_pps: int = 0
    errors_in: int = 0
    errors_out: int = 0
    discards_in: int = 0
    discards_out: int = 0
    utilization_in_percent: float = 0.0
    utilization_out_percent: float = 0.0
    last_state_change: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    @property
    def is_up(self) -> bool:
        """Verifica se a interface está up."""
        return self.status.lower() == "up"

    @property
    def is_down(self) -> bool:
        """Verifica se a interface está down."""
        return self.status.lower() in ["down", "admin_down"]

    @property
    def bandwidth_in_mbps(self) -> float:
        """Retorna a banda de entrada em Mbps."""
        return self.bandwidth_in_bps / 1_000_000

    @property
    def bandwidth_out_mbps(self) -> float:
        """Retorna a banda de saída em Mbps."""
        return self.bandwidth_out_bps / 1_000_000

    @property
    def bandwidth_in_gbps(self) -> float:
        """Retorna a banda de entrada em Gbps."""
        return self.bandwidth_in_bps / 1_000_000_000

    @property
    def bandwidth_out_gbps(self) -> float:
        """Retorna a banda de saída em Gbps."""
        return self.bandwidth_out_bps / 1_000_000_000

    @property
    def has_errors(self) -> bool:
        """Verifica se há erros na interface."""
        return (self.errors_in + self.errors_out) > 0

    @property
    def total_errors(self) -> int:
        """Retorna o total de erros (input + output)."""
        return self.errors_in + self.errors_out

    @property
    def total_discards(self) -> int:
        """Retorna o total de descartes (input + output)."""
        return self.discards_in + self.discards_out

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "is_up": self.is_up,
            "is_down": self.is_down,
            "bandwidth_capacity": self.bandwidth_capacity,
            "bandwidth_in_bps": self.bandwidth_in_bps,
            "bandwidth_out_bps": self.bandwidth_out_bps,
            "bandwidth_in_mbps": round(self.bandwidth_in_mbps, 2),
            "bandwidth_out_mbps": round(self.bandwidth_out_mbps, 2),
            "bandwidth_in_gbps": round(self.bandwidth_in_gbps, 4),
            "bandwidth_out_gbps": round(self.bandwidth_out_gbps, 4),
            "packets_in_pps": self.packets_in_pps,
            "packets_out_pps": self.packets_out_pps,
            "errors_in": self.errors_in,
            "errors_out": self.errors_out,
            "total_errors": self.total_errors,
            "discards_in": self.discards_in,
            "discards_out": self.discards_out,
            "total_discards": self.total_discards,
            "utilization_in_percent": round(self.utilization_in_percent, 2),
            "utilization_out_percent": round(self.utilization_out_percent, 2),
            "has_errors": self.has_errors,
            "last_state_change": (
                self.last_state_change.isoformat() if self.last_state_change else None
            ),
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class InterfaceTrafficHistory:
    """Representa um ponto no histórico de tráfego de interface."""

    interface_name: str
    bandwidth_in_bps: int = 0
    bandwidth_out_bps: int = 0
    packets_in_pps: int = 0
    packets_out_pps: int = 0
    errors_in: int = 0
    errors_out: int = 0
    utilization_in_percent: float = 0.0
    utilization_out_percent: float = 0.0
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> dict:
        """Converte o objeto para dicionário."""
        return {
            "id": self.id,
            "interface_name": self.interface_name,
            "bandwidth_in_bps": self.bandwidth_in_bps,
            "bandwidth_out_bps": self.bandwidth_out_bps,
            "packets_in_pps": self.packets_in_pps,
            "packets_out_pps": self.packets_out_pps,
            "errors_in": self.errors_in,
            "errors_out": self.errors_out,
            "utilization_in_percent": round(self.utilization_in_percent, 2),
            "utilization_out_percent": round(self.utilization_out_percent, 2),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
