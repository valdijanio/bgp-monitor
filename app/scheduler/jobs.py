"""
Jobs agendados para coleta periódica de dados.

Usa APScheduler para executar coletas em background.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.core.config import settings
from app.services.bgp_collector import collect_bgp_sessions, update_bgp_in_database
from app.services.interface_collector import collect_interfaces, update_interfaces_in_database
from app.services.alert_manager import check_all_alerts

logger = logging.getLogger(__name__)

# Instância global do scheduler
scheduler = AsyncIOScheduler()


def setup_scheduler() -> AsyncIOScheduler:
    """
    Configura e inicializa o scheduler com todos os jobs.

    Returns:
        Instância do scheduler configurado
    """
    logger.info("Configurando scheduler de coletas...")

    # Job de coleta BGP
    scheduler.add_job(
        job_collect_bgp,
        trigger=IntervalTrigger(seconds=settings.COLLECTION_INTERVAL_SECONDS),
        id="collect_bgp",
        name="Coletar sessões BGP",
        replace_existing=True,
        max_instances=1,
    )

    # Job de coleta de interfaces
    scheduler.add_job(
        job_collect_interfaces,
        trigger=IntervalTrigger(seconds=settings.COLLECTION_INTERVAL_SECONDS),
        id="collect_interfaces",
        name="Coletar interfaces",
        replace_existing=True,
        max_instances=1,
    )

    # Job de verificação de alertas (executa com menos frequência)
    alert_interval = settings.COLLECTION_INTERVAL_SECONDS * 2
    scheduler.add_job(
        job_check_alerts,
        trigger=IntervalTrigger(seconds=alert_interval),
        id="check_alerts",
        name="Verificar alertas",
        replace_existing=True,
        max_instances=1,
    )

    # Job de limpeza de dados antigos (1x por dia)
    scheduler.add_job(
        job_cleanup_old_data,
        trigger=IntervalTrigger(hours=24),
        id="cleanup_old_data",
        name="Limpar dados antigos",
        replace_existing=True,
        max_instances=1,
    )

    logger.info(f"Scheduler configurado com intervalo de {settings.COLLECTION_INTERVAL_SECONDS}s")
    return scheduler


def start_scheduler() -> None:
    """Inicia o scheduler."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler iniciado com sucesso")
        _log_scheduled_jobs()
    else:
        logger.warning("Scheduler já está em execução")


def stop_scheduler() -> None:
    """Para o scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler parado")
    else:
        logger.warning("Scheduler não está em execução")


def _log_scheduled_jobs() -> None:
    """Loga informações sobre os jobs agendados."""
    jobs = scheduler.get_jobs()
    logger.info(f"Jobs agendados: {len(jobs)}")
    for job in jobs:
        logger.info(f"  - {job.name} (ID: {job.id})")


# === Jobs ===


def job_collect_bgp() -> None:
    """Job para coletar sessões BGP."""
    try:
        logger.info("Iniciando job de coleta BGP...")
        start_time = datetime.now()

        # Coletar sessões
        sessions = collect_bgp_sessions()

        # Atualizar banco de dados
        update_bgp_in_database(sessions)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Job BGP concluído: {len(sessions)} sessões em {duration:.2f}s")

    except Exception as e:
        logger.error(f"Erro no job de coleta BGP: {e}", exc_info=True)


def job_collect_interfaces() -> None:
    """Job para coletar interfaces."""
    try:
        logger.info("Iniciando job de coleta de interfaces...")
        start_time = datetime.now()

        # Coletar interfaces
        interfaces = collect_interfaces()

        # Atualizar banco de dados
        update_interfaces_in_database(interfaces)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Job interfaces concluído: {len(interfaces)} interfaces em {duration:.2f}s")

    except Exception as e:
        logger.error(f"Erro no job de coleta de interfaces: {e}", exc_info=True)


def job_check_alerts() -> None:
    """Job para verificar alertas."""
    try:
        logger.info("Iniciando job de verificação de alertas...")
        start_time = datetime.now()

        # Verificar todos os alertas
        check_all_alerts()

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Job alertas concluído em {duration:.2f}s")

    except Exception as e:
        logger.error(f"Erro no job de verificação de alertas: {e}", exc_info=True)


def job_cleanup_old_data() -> None:
    """
    Job para limpar dados antigos do histórico.

    Remove registros de histórico com mais de 30 dias.
    """
    try:
        logger.info("Iniciando job de limpeza de dados antigos...")
        start_time = datetime.now()

        from app.core.database import db

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Limpar histórico BGP (>30 dias)
            cursor.execute(
                """
                DELETE FROM bgp_status_history
                WHERE datetime(timestamp) < datetime('now', '-30 days')
                """
            )
            bgp_deleted = cursor.rowcount

            # Limpar histórico de interfaces (>30 dias)
            cursor.execute(
                """
                DELETE FROM interface_traffic_history
                WHERE datetime(timestamp) < datetime('now', '-30 days')
                """
            )
            interface_deleted = cursor.rowcount

            # Limpar eventos antigos (>60 dias)
            cursor.execute(
                """
                DELETE FROM events
                WHERE datetime(timestamp) < datetime('now', '-60 days')
                """
            )
            events_deleted = cursor.rowcount

            conn.commit()

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Limpeza concluída em {duration:.2f}s: "
            f"{bgp_deleted} BGP history, "
            f"{interface_deleted} interface history, "
            f"{events_deleted} events removidos"
        )

    except Exception as e:
        logger.error(f"Erro no job de limpeza: {e}", exc_info=True)
