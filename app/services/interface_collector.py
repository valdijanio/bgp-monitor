"""
Collector para dados de interfaces do Huawei NE8000.

Coleta informações sobre interfaces e estatísticas de tráfego.
"""

import logging
from typing import List
from datetime import datetime

from app.core.ssh_client import ssh_client
from app.core.database import db
from app.models.interface import Interface
from app.services.parser import parse_interface, parse_interface_statistics

logger = logging.getLogger(__name__)


def collect_interfaces() -> List[Interface]:
    """
    Coleta informações de todas as interfaces.

    Executa 'display interface' no NE8000 e parseia o resultado.

    Returns:
        Lista de Interface coletadas

    Raises:
        Exception: Se houver erro na coleta
    """
    logger.info("Iniciando coleta de interfaces...")

    try:
        # Executar comando no NE8000
        output = ssh_client.execute_command("display interface")

        # Parsear saída
        interfaces = parse_interface(output)

        logger.info(f"Coletadas {len(interfaces)} interfaces")

        # Para cada interface, tentar coletar estatísticas
        for interface in interfaces:
            try:
                stats = collect_interface_statistics(interface.name)

                # Atualizar interface com estatísticas
                interface.bandwidth_capacity = stats["bandwidth_capacity"]
                interface.bandwidth_in_bps = stats["bandwidth_in_bps"]
                interface.bandwidth_out_bps = stats["bandwidth_out_bps"]
                interface.packets_in_pps = stats["packets_in_pps"]
                interface.packets_out_pps = stats["packets_out_pps"]
                interface.errors_in = stats["errors_in"]
                interface.errors_out = stats["errors_out"]
                interface.discards_in = stats["discards_in"]
                interface.discards_out = stats["discards_out"]

                # Calcular utilização percentual
                if interface.bandwidth_capacity > 0:
                    interface.utilization_in_percent = (
                        interface.bandwidth_in_bps / interface.bandwidth_capacity
                    ) * 100
                    interface.utilization_out_percent = (
                        interface.bandwidth_out_bps / interface.bandwidth_capacity
                    ) * 100

            except Exception as e:
                logger.warning(f"Erro ao coletar estatísticas de {interface.name}: {e}")

        return interfaces

    except Exception as e:
        logger.error(f"Erro ao coletar interfaces: {e}")
        raise


def collect_interface_statistics(interface_name: str) -> dict:
    """
    Coleta estatísticas detalhadas de uma interface específica.

    Args:
        interface_name: Nome da interface

    Returns:
        Dicionário com estatísticas
    """
    try:
        command = f"display interface {interface_name}"
        output = ssh_client.execute_command(command)
        return parse_interface_statistics(output, interface_name)
    except Exception as e:
        logger.warning(f"Erro ao coletar estatísticas de {interface_name}: {e}")
        return {
            "bandwidth_in_bps": 0,
            "bandwidth_out_bps": 0,
            "packets_in_pps": 0,
            "packets_out_pps": 0,
            "errors_in": 0,
            "errors_out": 0,
            "discards_in": 0,
            "discards_out": 0,
            "bandwidth_capacity": 0,
        }


def update_interfaces_in_database(interfaces: List[Interface]) -> None:
    """
    Atualiza/insere interfaces no banco de dados.

    Detecta mudanças de estado e gera eventos.
    Usa transação atômica para garantir consistência.

    Args:
        interfaces: Lista de interfaces coletadas
    """
    if not interfaces:
        logger.warning("Nenhuma interface para atualizar no banco")
        return

    logger.info(f"Atualizando {len(interfaces)} interfaces no banco de dados...")

    with db.get_connection() as conn:
        cursor = conn.cursor()

        for interface in interfaces:
            try:
                # Verificar se interface já existe
                cursor.execute(
                    "SELECT name, status FROM interfaces WHERE name = ?", (interface.name,)
                )
                existing = cursor.fetchone()

                current_time = datetime.now().isoformat()

                if existing:
                    # Interface existe - verificar mudança de estado
                    old_status = existing[1]

                    if old_status != interface.status:
                        # Mudança de estado - gerar evento
                        logger.info(
                            f"Interface {interface.name}: {old_status} -> {interface.status}"
                        )

                        _create_interface_event(
                            cursor, interface.name, old_status, interface.status, current_time
                        )

                    # Atualizar interface
                    cursor.execute(
                        """
                        UPDATE interfaces
                        SET description = ?, status = ?, bandwidth_capacity = ?,
                            bandwidth_in_bps = ?, bandwidth_out_bps = ?,
                            packets_in_pps = ?, packets_out_pps = ?,
                            errors_in = ?, errors_out = ?,
                            discards_in = ?, discards_out = ?,
                            utilization_in_percent = ?, utilization_out_percent = ?,
                            last_updated = ?
                        WHERE name = ?
                        """,
                        (
                            interface.description,
                            interface.status,
                            interface.bandwidth_capacity,
                            interface.bandwidth_in_bps,
                            interface.bandwidth_out_bps,
                            interface.packets_in_pps,
                            interface.packets_out_pps,
                            interface.errors_in,
                            interface.errors_out,
                            interface.discards_in,
                            interface.discards_out,
                            interface.utilization_in_percent,
                            interface.utilization_out_percent,
                            current_time,
                            interface.name,
                        ),
                    )
                else:
                    # Nova interface - inserir
                    logger.info(f"Nova interface descoberta: {interface.name}")

                    cursor.execute(
                        """
                        INSERT INTO interfaces
                        (name, description, status, bandwidth_capacity,
                         bandwidth_in_bps, bandwidth_out_bps,
                         packets_in_pps, packets_out_pps,
                         errors_in, errors_out, discards_in, discards_out,
                         utilization_in_percent, utilization_out_percent,
                         last_state_change, last_updated, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            interface.name,
                            interface.description,
                            interface.status,
                            interface.bandwidth_capacity,
                            interface.bandwidth_in_bps,
                            interface.bandwidth_out_bps,
                            interface.packets_in_pps,
                            interface.packets_out_pps,
                            interface.errors_in,
                            interface.errors_out,
                            interface.discards_in,
                            interface.discards_out,
                            interface.utilization_in_percent,
                            interface.utilization_out_percent,
                            current_time,
                            current_time,
                            current_time,
                        ),
                    )

                # Gravar histórico
                cursor.execute(
                    """
                    INSERT INTO interface_traffic_history
                    (interface_name, bandwidth_in_bps, bandwidth_out_bps,
                     packets_in_pps, packets_out_pps, errors_in, errors_out,
                     utilization_in_percent, utilization_out_percent, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        interface.name,
                        interface.bandwidth_in_bps,
                        interface.bandwidth_out_bps,
                        interface.packets_in_pps,
                        interface.packets_out_pps,
                        interface.errors_in,
                        interface.errors_out,
                        interface.utilization_in_percent,
                        interface.utilization_out_percent,
                        current_time,
                    ),
                )

            except Exception as e:
                logger.error(f"Erro ao atualizar interface {interface.name}: {e}")
                # Propagar exceção para rollback
                raise

        # Commit explícito
        conn.commit()
        logger.info("Interfaces atualizadas com sucesso no banco")


def _create_interface_event(
    cursor, interface_name: str, old_status: str, new_status: str, timestamp: str
) -> None:
    """
    Cria um evento de mudança de estado de interface.

    Args:
        cursor: Cursor do banco de dados
        interface_name: Nome da interface
        old_status: Status anterior
        new_status: Novo status
        timestamp: Timestamp do evento
    """
    # Determinar tipo e severidade
    if new_status.lower() == "up":
        event_type = "interface_up"
        severity = "info"
    elif new_status.lower() in ["down", "admin_down"]:
        event_type = "interface_down"
        severity = "critical"
    else:
        event_type = "interface_flapping"
        severity = "warning"

    message = f"Interface {interface_name} mudou de {old_status} para {new_status}"
    details = f"Interface: {interface_name}, Old status: {old_status}, New status: {new_status}"

    cursor.execute(
        """
        INSERT INTO events
        (timestamp, event_type, severity, source, message, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (timestamp, event_type, severity, f"Interface:{interface_name}", message, details),
    )

    logger.info(f"Evento de interface criado: {message}")
