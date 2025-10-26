"""
API endpoints para eventos do sistema.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["Events"])


# Pydantic models para respostas
class EventResponse(BaseModel):
    """Modelo de resposta para evento."""

    id: int
    timestamp: str
    event_type: str
    severity: str
    source: str
    message: str
    details: Optional[str]


@router.get("", response_model=List[EventResponse])
async def get_events(
    event_type: Optional[str] = Query(
        None, description="Filtrar por tipo (bgp_up, bgp_down, interface_up, etc)"
    ),
    severity: Optional[str] = Query(
        None, description="Filtrar por severidade (critical, warning, info)"
    ),
    source: Optional[str] = Query(None, description="Filtrar por fonte"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
):
    """
    Lista eventos do sistema.

    Args:
        event_type: Filtro opcional por tipo de evento
        severity: Filtro opcional por severidade
        source: Filtro opcional por fonte
        limit: Limite de resultados

    Returns:
        Lista de eventos
    """
    try:
        # Construir query com filtros dinâmicos
        conditions = []
        params = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)

        if severity:
            conditions.append("severity = ?")
            params.append(severity)

        if source:
            conditions.append("source LIKE ?")
            params.append(f"%{source}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM events
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT {limit}
        """

        events = db.execute_query(query, tuple(params) if params else None)

        return events

    except Exception as e:
        logger.error(f"Erro ao buscar eventos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar eventos")


@router.get("/recent", response_model=List[EventResponse])
async def get_recent_events(limit: int = Query(50, ge=1, le=200, description="Número de eventos")):
    """
    Obtém os eventos mais recentes.

    Args:
        limit: Número de eventos a retornar

    Returns:
        Eventos mais recentes
    """
    try:
        query = f"""
            SELECT * FROM events
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        events = db.execute_query(query)

        return events

    except Exception as e:
        logger.error(f"Erro ao buscar eventos recentes: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar eventos recentes")


@router.get("/critical", response_model=List[EventResponse])
async def get_critical_events(
    limit: int = Query(50, ge=1, le=200, description="Número de eventos")
):
    """
    Obtém apenas eventos críticos.

    Args:
        limit: Número de eventos a retornar

    Returns:
        Eventos críticos
    """
    try:
        query = f"""
            SELECT * FROM events
            WHERE severity = 'critical'
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        events = db.execute_query(query)

        return events

    except Exception as e:
        logger.error(f"Erro ao buscar eventos críticos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar eventos críticos")


@router.get("/stats")
async def get_events_stats():
    """
    Obtém estatísticas sobre eventos.

    Returns:
        Estatísticas de eventos
    """
    try:
        # Total de eventos
        total_query = "SELECT COUNT(*) as count FROM events"
        total_result = db.execute_single(total_query)
        total_events = total_result["count"] if total_result else 0

        # Eventos por severidade
        severity_query = """
            SELECT severity, COUNT(*) as count
            FROM events
            GROUP BY severity
        """
        severity_counts = db.execute_query(severity_query)

        # Eventos por tipo
        type_query = """
            SELECT event_type, COUNT(*) as count
            FROM events
            GROUP BY event_type
            ORDER BY count DESC
            LIMIT 10
        """
        type_counts = db.execute_query(type_query)

        # Eventos nas últimas 24h
        recent_query = """
            SELECT COUNT(*) as count
            FROM events
            WHERE datetime(timestamp) > datetime('now', '-24 hours')
        """
        recent_result = db.execute_single(recent_query)
        recent_events = recent_result["count"] if recent_result else 0

        return {
            "total_events": total_events,
            "events_last_24h": recent_events,
            "by_severity": {item["severity"]: item["count"] for item in severity_counts},
            "by_type": {item["event_type"]: item["count"] for item in type_counts},
        }

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas de eventos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar estatísticas")
