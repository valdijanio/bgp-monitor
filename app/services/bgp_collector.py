"""
Collector para dados BGP do Huawei NE8000.

Coleta informações sobre sessões BGP e salva no banco de dados.
"""

import logging
from typing import List
from datetime import datetime

from app.core.ssh_client import ssh_client
from app.core.database import db
from app.models.bgp import BGPSession
from app.services.parser import parse_bgp_peer, parse_bgp_routing_table_peer

logger = logging.getLogger(__name__)


def collect_bgp_sessions() -> List[BGPSession]:
    """
    Coleta informações de todas as sessões BGP.

    Executa 'display bgp peer' no NE8000 e parseia o resultado.

    Returns:
        Lista de BGPSession coletadas

    Raises:
        Exception: Se houver erro na coleta
    """
    logger.info("Iniciando coleta de sessões BGP...")

    try:
        # Executar comando no NE8000
        output = ssh_client.execute_command("display bgp peer")

        # Parsear saída
        sessions = parse_bgp_peer(output)

        logger.info(f"Coletadas {len(sessions)} sessões BGP")

        # Para cada sessão, tentar coletar prefixos
        for session in sessions:
            try:
                prefixes = collect_bgp_prefixes(session.peer_ip)
                session.prefixes_received = prefixes["prefixes_received"]
                session.prefixes_sent = prefixes["prefixes_sent"]
            except Exception as e:
                logger.warning(f"Erro ao coletar prefixos para {session.peer_ip}: {e}")

        return sessions

    except Exception as e:
        logger.error(f"Erro ao coletar sessões BGP: {e}")
        raise


def collect_bgp_prefixes(peer_ip: str) -> dict:
    """
    Coleta número de prefixos recebidos/enviados de um peer específico.

    Args:
        peer_ip: IP do peer BGP

    Returns:
        Dicionário com 'prefixes_received' e 'prefixes_sent'
    """
    try:
        command = f"display bgp routing-table peer {peer_ip}"
        output = ssh_client.execute_command(command)
        return parse_bgp_routing_table_peer(output, peer_ip)
    except Exception as e:
        logger.warning(f"Erro ao coletar prefixos de {peer_ip}: {e}")
        return {"prefixes_received": 0, "prefixes_sent": 0}


def update_bgp_in_database(sessions: List[BGPSession]) -> None:
    """
    Atualiza/insere sessões BGP no banco de dados.

    Detecta mudanças de estado e gera eventos.
    Usa transação atômica para garantir consistência.

    Args:
        sessions: Lista de sessões BGP coletadas
    """
    if not sessions:
        logger.warning("Nenhuma sessão BGP para atualizar no banco")
        return

    logger.info(f"Atualizando {len(sessions)} sessões BGP no banco de dados...")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        for session in sessions:
            try:
                # Verificar se sessão já existe
                cursor.execute(
                    "SELECT peer_ip, status FROM bgp_sessions WHERE peer_ip = ?",
                    (session.peer_ip,),
                )
                existing = cursor.fetchone()

                current_time = datetime.now().isoformat()

                if existing:
                    # Sessão existe - verificar mudança de estado
                    old_status = existing[1]

                    if old_status != session.status:
                        # Mudança de estado - gerar evento
                        logger.info(f"BGP peer {session.peer_ip}: {old_status} -> {session.status}")

                        _create_bgp_event(
                            cursor, session.peer_ip, old_status, session.status, current_time
                        )

                    # Atualizar sessão
                    cursor.execute(
                        """
                        UPDATE bgp_sessions
                        SET status = ?, uptime_seconds = ?, prefixes_received = ?,
                            prefixes_sent = ?, last_updated = ?
                        WHERE peer_ip = ?
                        """,
                        (
                            session.status,
                            session.uptime_seconds,
                            session.prefixes_received,
                            session.prefixes_sent,
                            current_time,
                            session.peer_ip,
                        ),
                    )
                else:
                    # Nova sessão - inserir
                    logger.info(f"Nova sessão BGP descoberta: {session.peer_ip}")

                    cursor.execute(
                        """
                        INSERT INTO bgp_sessions
                        (peer_ip, peer_asn, peer_description, status, uptime_seconds,
                         prefixes_received, prefixes_sent, last_state_change,
                         last_updated, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session.peer_ip,
                            session.peer_asn,
                            session.peer_description,
                            session.status,
                            session.uptime_seconds,
                            session.prefixes_received,
                            session.prefixes_sent,
                            current_time,
                            current_time,
                            current_time,
                        ),
                    )

                # Gravar histórico
                cursor.execute(
                    """
                    INSERT INTO bgp_status_history
                    (peer_ip, status, prefixes_received, prefixes_sent, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        session.peer_ip,
                        session.status,
                        session.prefixes_received,
                        session.prefixes_sent,
                        current_time,
                    ),
                )

            except Exception as e:
                logger.error(f"Erro ao atualizar BGP session {session.peer_ip}: {e}")
                # Propagar exceção para rollback
                raise

        # Commit explícito
        conn.commit()
        logger.info("Sessões BGP atualizadas com sucesso no banco")


def _create_bgp_event(
    cursor, peer_ip: str, old_status: str, new_status: str, timestamp: str
) -> None:
    """
    Cria um evento de mudança de estado BGP.

    Args:
        cursor: Cursor do banco de dados
        peer_ip: IP do peer
        old_status: Status anterior
        new_status: Novo status
        timestamp: Timestamp do evento
    """
    # Determinar tipo e severidade
    if new_status.lower() == "established":
        event_type = "bgp_up"
        severity = "info"
    elif new_status.lower() == "down":
        event_type = "bgp_down"
        severity = "critical"
    else:
        event_type = "bgp_flapping"
        severity = "warning"

    message = f"BGP peer {peer_ip} mudou de {old_status} para {new_status}"
    details = f"Peer IP: {peer_ip}, Old status: {old_status}, New status: {new_status}"

    cursor.execute(
        """
        INSERT INTO events
        (timestamp, event_type, severity, source, message, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (timestamp, event_type, severity, f"BGP:{peer_ip}", message, details),
    )

    logger.info(f"Evento BGP criado: {message}")
