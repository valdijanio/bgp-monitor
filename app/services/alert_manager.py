"""
Gerenciador de alertas do BGP Monitor.

Verifica condições de alerta e gera eventos no banco de dados.
"""

import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import db

logger = logging.getLogger(__name__)


def check_all_alerts() -> None:
    """
    Executa todas as verificações de alertas configuradas.

    Verifica:
    - Sessões BGP down
    - Interfaces down
    - Limites de erros excedidos
    """
    logger.info("Verificando alertas...")

    try:
        if settings.ALERT_BGP_DOWN_ENABLED:
            check_bgp_alerts()

        if settings.ALERT_INTERFACE_DOWN_ENABLED:
            check_interface_alerts()

        check_error_thresholds()

        logger.info("Verificação de alertas concluída")

    except Exception as e:
        logger.error(f"Erro ao verificar alertas: {e}")


def check_bgp_alerts() -> None:
    """
    Verifica se há sessões BGP em estado crítico.

    Gera alertas para sessões que não estão Established.
    """
    try:
        query = """
            SELECT peer_ip, peer_asn, status, uptime_seconds
            FROM bgp_sessions
            WHERE status != 'Established'
        """

        down_sessions = db.execute_query(query)

        if down_sessions:
            logger.warning(f"Encontradas {len(down_sessions)} sessões BGP não established")

            for session in down_sessions:
                peer_ip = session["peer_ip"]
                status = session["status"]

                # Verificar se já não existe evento recente (últimos 5 minutos)
                if not _has_recent_event("bgp_down", peer_ip, minutes=5):
                    create_event(
                        event_type="bgp_down",
                        severity="critical",
                        source=f"BGP:{peer_ip}",
                        message=f"Sessão BGP {peer_ip} está {status}",
                        details=f"ASN: {session['peer_asn']}, "
                        f"Status: {status}, "
                        f"Uptime: {session['uptime_seconds']}s",
                    )
        else:
            logger.debug("Todas as sessões BGP estão Established")

    except Exception as e:
        logger.error(f"Erro ao verificar alertas BGP: {e}")


def check_interface_alerts() -> None:
    """
    Verifica se há interfaces em estado crítico.

    Gera alertas para interfaces down.
    """
    try:
        query = """
            SELECT name, description, status
            FROM interfaces
            WHERE status IN ('down', 'admin_down')
        """

        down_interfaces = db.execute_query(query)

        if down_interfaces:
            logger.warning(f"Encontradas {len(down_interfaces)} interfaces down")

            for interface in down_interfaces:
                interface_name = interface["name"]
                status = interface["status"]

                # Verificar se já não existe evento recente (últimos 5 minutos)
                if not _has_recent_event("interface_down", interface_name, minutes=5):
                    create_event(
                        event_type="interface_down",
                        severity="critical",
                        source=f"Interface:{interface_name}",
                        message=f"Interface {interface_name} está {status}",
                        details=f"Description: {interface['description']}, Status: {status}",
                    )
        else:
            logger.debug("Todas as interfaces monitoradas estão UP")

    except Exception as e:
        logger.error(f"Erro ao verificar alertas de interfaces: {e}")


def check_error_thresholds() -> None:
    """
    Verifica se alguma interface excedeu o limite de erros configurado.

    Gera alertas quando errors_in + errors_out > ALERT_ERROR_THRESHOLD.
    """
    try:
        threshold = settings.ALERT_ERROR_THRESHOLD

        query = f"""
            SELECT name, description, errors_in, errors_out,
                   (errors_in + errors_out) as total_errors
            FROM interfaces
            WHERE (errors_in + errors_out) > {threshold}
            AND status = 'up'
        """

        high_error_interfaces = db.execute_query(query)

        if high_error_interfaces:
            logger.warning(f"Encontradas {len(high_error_interfaces)} interfaces com erros altos")

            for interface in high_error_interfaces:
                interface_name = interface["name"]
                total_errors = interface["total_errors"]

                # Verificar se já não existe evento recente (últimos 10 minutos)
                if not _has_recent_event("high_errors", interface_name, minutes=10):
                    create_event(
                        event_type="high_errors",
                        severity="warning",
                        source=f"Interface:{interface_name}",
                        message=f"Interface {interface_name} com alto nível de erros",
                        details=f"Total de erros: {total_errors}, "
                        f"Threshold: {threshold}, "
                        f"Input errors: {interface['errors_in']}, "
                        f"Output errors: {interface['errors_out']}",
                    )

    except Exception as e:
        logger.error(f"Erro ao verificar limites de erros: {e}")


def create_event(
    event_type: str, severity: str, source: str, message: str, details: str = None
) -> None:
    """
    Cria um novo evento no banco de dados.

    Args:
        event_type: Tipo do evento (bgp_down, interface_down, etc)
        severity: Severidade (critical, warning, info)
        source: Origem do evento
        message: Mensagem descritiva
        details: Detalhes adicionais (opcional)
    """
    try:
        timestamp = datetime.now().isoformat()

        query = """
            INSERT INTO events
            (timestamp, event_type, severity, source, message, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        db.execute_write(query, (timestamp, event_type, severity, source, message, details))

        logger.info(f"Evento criado: [{severity}] {message}")

    except Exception as e:
        logger.error(f"Erro ao criar evento: {e}")


def _has_recent_event(event_type: str, source_filter: str, minutes: int = 5) -> bool:
    """
    Verifica se já existe um evento recente do mesmo tipo e fonte.

    Evita duplicação de alertas.

    Args:
        event_type: Tipo do evento
        source_filter: Parte do source para filtrar
        minutes: Janela de tempo em minutos

    Returns:
        True se existe evento recente, False caso contrário
    """
    try:
        query = f"""
            SELECT COUNT(*) as count
            FROM events
            WHERE event_type = ?
            AND source LIKE ?
            AND datetime(timestamp) > datetime('now', '-{minutes} minutes')
        """

        result = db.execute_single(query, (event_type, f"%{source_filter}%"))

        if result and result["count"] > 0:
            return True

        return False

    except Exception as e:
        logger.error(f"Erro ao verificar evento recente: {e}")
        return False
