"""
API endpoints para dados BGP.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bgp", tags=["BGP"])


# Pydantic models para respostas
class BGPSessionResponse(BaseModel):
    """Modelo de resposta para sessão BGP."""

    id: Optional[int]
    peer_ip: str
    peer_asn: str
    peer_description: Optional[str]
    status: str
    uptime_seconds: int
    uptime_hours: float
    uptime_days: float
    prefixes_received: int
    prefixes_sent: int
    last_state_change: Optional[str]
    last_updated: Optional[str]
    created_at: Optional[str]


class BGPStatsResponse(BaseModel):
    """Modelo de resposta para estatísticas gerais BGP."""

    total_sessions: int
    established_sessions: int
    down_sessions: int
    other_sessions: int
    total_prefixes_received: int
    total_prefixes_sent: int


class BGPHistoryResponse(BaseModel):
    """Modelo de resposta para histórico BGP."""

    id: int
    peer_ip: str
    status: str
    prefixes_received: int
    prefixes_sent: int
    timestamp: str


@router.get("/sessions", response_model=List[BGPSessionResponse])
async def get_bgp_sessions(
    status: Optional[str] = Query(None, description="Filtrar por status (Established, Down, etc)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
):
    """
    Lista todas as sessões BGP.

    Args:
        status: Filtro opcional por status
        limit: Limite de resultados

    Returns:
        Lista de sessões BGP
    """
    try:
        if status:
            query = f"SELECT * FROM bgp_sessions WHERE status = ? ORDER BY peer_ip LIMIT {limit}"
            sessions = db.execute_query(query, (status,))
        else:
            query = f"SELECT * FROM bgp_sessions ORDER BY peer_ip LIMIT {limit}"
            sessions = db.execute_query(query)

        # Calcular uptime em horas e dias
        for session in sessions:
            session["uptime_hours"] = round(session["uptime_seconds"] / 3600, 2)
            session["uptime_days"] = round(session["uptime_seconds"] / 86400, 2)

        return sessions

    except Exception as e:
        logger.error(f"Erro ao buscar sessões BGP: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sessões BGP")


@router.get("/sessions/{peer_ip}", response_model=BGPSessionResponse)
async def get_bgp_session(peer_ip: str):
    """
    Obtém detalhes de uma sessão BGP específica.

    Args:
        peer_ip: IP do peer BGP

    Returns:
        Detalhes da sessão BGP
    """
    try:
        query = "SELECT * FROM bgp_sessions WHERE peer_ip = ?"
        session = db.execute_single(query, (peer_ip,))

        if not session:
            raise HTTPException(status_code=404, detail=f"Sessão BGP {peer_ip} não encontrada")

        # Calcular uptime em horas e dias
        session["uptime_hours"] = round(session["uptime_seconds"] / 3600, 2)
        session["uptime_days"] = round(session["uptime_seconds"] / 86400, 2)

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar sessão BGP {peer_ip}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar sessão BGP")


@router.get("/stats", response_model=BGPStatsResponse)
async def get_bgp_stats():
    """
    Obtém estatísticas gerais de todas as sessões BGP.

    Returns:
        Estatísticas agregadas
    """
    try:
        # Total de sessões
        total_query = "SELECT COUNT(*) as count FROM bgp_sessions"
        total_result = db.execute_single(total_query)
        total_sessions = total_result["count"] if total_result else 0

        # Sessões estabelecidas
        established_query = (
            "SELECT COUNT(*) as count FROM bgp_sessions WHERE status = 'Established'"
        )
        established_result = db.execute_single(established_query)
        established_sessions = established_result["count"] if established_result else 0

        # Sessões down
        down_query = "SELECT COUNT(*) as count FROM bgp_sessions WHERE status = 'Down'"
        down_result = db.execute_single(down_query)
        down_sessions = down_result["count"] if down_result else 0

        # Outras sessões
        other_sessions = total_sessions - established_sessions - down_sessions

        # Total de prefixos
        prefixes_query = """
            SELECT
                COALESCE(SUM(prefixes_received), 0) as total_received,
                COALESCE(SUM(prefixes_sent), 0) as total_sent
            FROM bgp_sessions
        """
        prefixes_result = db.execute_single(prefixes_query)

        return {
            "total_sessions": total_sessions,
            "established_sessions": established_sessions,
            "down_sessions": down_sessions,
            "other_sessions": other_sessions,
            "total_prefixes_received": prefixes_result["total_received"] if prefixes_result else 0,
            "total_prefixes_sent": prefixes_result["total_sent"] if prefixes_result else 0,
        }

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas BGP: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar estatísticas BGP")


@router.get("/history/{peer_ip}", response_model=List[BGPHistoryResponse])
async def get_bgp_history(
    peer_ip: str,
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
):
    """
    Obtém histórico de uma sessão BGP específica.

    Args:
        peer_ip: IP do peer BGP
        limit: Limite de resultados

    Returns:
        Histórico da sessão
    """
    try:
        query = f"""
            SELECT * FROM bgp_status_history
            WHERE peer_ip = ?
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        history = db.execute_query(query, (peer_ip,))

        # Retornar lista vazia se não houver histórico (não é erro)
        if not history:
            logger.info(f"Nenhum histórico encontrado para peer {peer_ip}")
            return []

        return history

    except Exception as e:
        logger.error(f"Erro ao buscar histórico BGP de {peer_ip}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico BGP")
