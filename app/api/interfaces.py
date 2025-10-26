"""
API endpoints para dados de interfaces.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interfaces", tags=["Interfaces"])


# Pydantic models para respostas
class InterfaceResponse(BaseModel):
    """Modelo de resposta para interface."""

    id: Optional[int]
    name: str
    description: Optional[str]
    status: str
    bandwidth_capacity: int
    bandwidth_in_bps: int
    bandwidth_out_bps: int
    bandwidth_in_mbps: float
    bandwidth_out_mbps: float
    bandwidth_in_gbps: float
    bandwidth_out_gbps: float
    packets_in_pps: int
    packets_out_pps: int
    errors_in: int
    errors_out: int
    total_errors: int
    discards_in: int
    discards_out: int
    total_discards: int
    utilization_in_percent: float
    utilization_out_percent: float
    last_state_change: Optional[str]
    last_updated: Optional[str]
    created_at: Optional[str]


class InterfaceStatsResponse(BaseModel):
    """Modelo de resposta para estatísticas de interface."""

    name: str
    bandwidth_in_bps: int
    bandwidth_out_bps: int
    packets_in_pps: int
    packets_out_pps: int
    errors_in: int
    errors_out: int
    utilization_in_percent: float
    utilization_out_percent: float


class InterfaceHistoryResponse(BaseModel):
    """Modelo de resposta para histórico de interface."""

    id: int
    interface_name: str
    bandwidth_in_bps: int
    bandwidth_out_bps: int
    packets_in_pps: int
    packets_out_pps: int
    errors_in: int
    errors_out: int
    utilization_in_percent: float
    utilization_out_percent: float
    timestamp: str


@router.get("", response_model=List[InterfaceResponse])
async def get_interfaces(
    status: Optional[str] = Query(None, description="Filtrar por status (up, down, admin_down)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
):
    """
    Lista todas as interfaces.

    Args:
        status: Filtro opcional por status
        limit: Limite de resultados

    Returns:
        Lista de interfaces
    """
    try:
        if status:
            query = f"SELECT * FROM interfaces WHERE status = ? ORDER BY name LIMIT {limit}"
            interfaces = db.execute_query(query, (status,))
        else:
            query = f"SELECT * FROM interfaces ORDER BY name LIMIT {limit}"
            interfaces = db.execute_query(query)

        # Calcular conversões de unidades
        for interface in interfaces:
            interface["bandwidth_in_mbps"] = round(interface["bandwidth_in_bps"] / 1_000_000, 2)
            interface["bandwidth_out_mbps"] = round(interface["bandwidth_out_bps"] / 1_000_000, 2)
            interface["bandwidth_in_gbps"] = round(interface["bandwidth_in_bps"] / 1_000_000_000, 4)
            interface["bandwidth_out_gbps"] = round(
                interface["bandwidth_out_bps"] / 1_000_000_000, 4
            )
            interface["total_errors"] = interface["errors_in"] + interface["errors_out"]
            interface["total_discards"] = interface["discards_in"] + interface["discards_out"]

        return interfaces

    except Exception as e:
        logger.error(f"Erro ao buscar interfaces: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar interfaces")


@router.get("/{name}", response_model=InterfaceResponse)
async def get_interface(name: str):
    """
    Obtém detalhes de uma interface específica.

    Args:
        name: Nome da interface

    Returns:
        Detalhes da interface
    """
    try:
        query = "SELECT * FROM interfaces WHERE name = ?"
        interface = db.execute_single(query, (name,))

        if not interface:
            raise HTTPException(status_code=404, detail=f"Interface {name} não encontrada")

        # Calcular conversões de unidades
        interface["bandwidth_in_mbps"] = round(interface["bandwidth_in_bps"] / 1_000_000, 2)
        interface["bandwidth_out_mbps"] = round(interface["bandwidth_out_bps"] / 1_000_000, 2)
        interface["bandwidth_in_gbps"] = round(interface["bandwidth_in_bps"] / 1_000_000_000, 4)
        interface["bandwidth_out_gbps"] = round(interface["bandwidth_out_bps"] / 1_000_000_000, 4)
        interface["total_errors"] = interface["errors_in"] + interface["errors_out"]
        interface["total_discards"] = interface["discards_in"] + interface["discards_out"]

        return interface

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar interface {name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar interface")


@router.get("/{name}/stats", response_model=InterfaceStatsResponse)
async def get_interface_stats(name: str):
    """
    Obtém estatísticas de uma interface específica.

    Args:
        name: Nome da interface

    Returns:
        Estatísticas da interface
    """
    try:
        query = """
            SELECT name, bandwidth_in_bps, bandwidth_out_bps,
                   packets_in_pps, packets_out_pps, errors_in, errors_out,
                   utilization_in_percent, utilization_out_percent
            FROM interfaces
            WHERE name = ?
        """
        stats = db.execute_single(query, (name,))

        if not stats:
            raise HTTPException(status_code=404, detail=f"Interface {name} não encontrada")

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas de {name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar estatísticas")


@router.get("/{name}/history", response_model=List[InterfaceHistoryResponse])
async def get_interface_history(
    name: str,
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
):
    """
    Obtém histórico de uma interface específica.

    Args:
        name: Nome da interface
        limit: Limite de resultados

    Returns:
        Histórico da interface
    """
    try:
        query = f"""
            SELECT * FROM interface_traffic_history
            WHERE interface_name = ?
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        history = db.execute_query(query, (name,))

        if not history:
            raise HTTPException(status_code=404, detail=f"Sem histórico para interface {name}")

        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar histórico de {name}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico")
