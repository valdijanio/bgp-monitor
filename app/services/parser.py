"""
Parsers para saída de comandos CLI do Huawei NE8000.

Este módulo contém funções para extrair dados estruturados dos comandos 'display'.
"""

import re
import logging
from typing import List, Dict, Any

from app.models.bgp import BGPSession
from app.models.interface import Interface

logger = logging.getLogger(__name__)


def parse_bgp_peer(output: str) -> List[BGPSession]:  # noqa: C901
    """
    Parseia a saída do comando 'display bgp peer'.

    Formato esperado (exemplo Huawei VRP):
    BGP local router ID : 192.168.1.1
    Local AS number : 65000
    Total number of peers : 5           Peers in established state : 3

     Peer            V    AS  MsgRcvd  MsgSent  OutQ  Up/Down       State
     10.0.0.1        4 65001   123456   123457     0  00:05:23   Established
     10.0.0.2        4 65002        0        0     0  00:00:00      Idle

    Args:
        output: Saída do comando display bgp peer

    Returns:
        Lista de objetos BGPSession (vazia se não houver peers)
    """
    sessions = []

    try:
        # Dividir em linhas
        lines = output.strip().split("\n")

        # Verificar se há realmente dados BGP
        has_bgp_data = False
        for line in lines:
            if "BGP" in line or "Peer" in line or any(c.isdigit() for c in line):
                has_bgp_data = True
                break

        if not has_bgp_data:
            logger.info("Nenhum dado BGP encontrado no output (BGP pode não estar configurado)")
            return sessions

        for line in lines:
            line = line.strip()

            # Pular linhas vazias, cabeçalhos e prompts
            if not line or "Peer" in line or "BGP" in line or "---" in line:
                continue
            if line.startswith("<") or line.startswith(">"):
                continue

            # Tentar parsear linha de peer
            # Formato: IP  Version  ASN  MsgRcvd  MsgSent  OutQ  Uptime  State
            match = re.match(
                r"^([\d\.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d:]+|Never)\s+(\w+)",
                line,
            )

            if match:
                peer_ip = match.group(1)
                asn = match.group(3)
                uptime_str = match.group(7)
                status = match.group(8)

                # Converter uptime para segundos
                uptime_seconds = _parse_uptime(uptime_str)

                session = BGPSession(
                    peer_ip=peer_ip,
                    peer_asn=asn,
                    status=status,
                    uptime_seconds=uptime_seconds,
                    prefixes_received=0,  # Será obtido por outro comando
                    prefixes_sent=0,
                )

                sessions.append(session)
                logger.debug(f"BGP peer parseado: {peer_ip} - {status}")

        if len(sessions) == 0:
            logger.info("Nenhuma sessão BGP foi parseada (BGP pode não ter peers configurados)")

    except Exception as e:
        logger.error(f"Erro ao parsear BGP peer: {e}")
        logger.debug(f"Output problemático: {output}")

    return sessions


def parse_bgp_routing_table_peer(output: str, peer_ip: str) -> Dict[str, int]:
    """
    Parseia a saída do comando 'display bgp routing-table peer <IP>'.

    Extrai o número de prefixos recebidos e anunciados.

    Args:
        output: Saída do comando
        peer_ip: IP do peer

    Returns:
        Dicionário com 'prefixes_received' e 'prefixes_sent'
    """
    result = {"prefixes_received": 0, "prefixes_sent": 0}

    try:
        # Procurar por padrões como:
        # "Total number of routes: 150"
        # "Number of routes received: 150"
        # "Number of routes advertised: 100"

        received_match = re.search(r"(?:received|Received).*?:\s*(\d+)", output, re.IGNORECASE)
        advertised_match = re.search(r"(?:advertised|Sent|sent).*?:\s*(\d+)", output, re.IGNORECASE)

        if received_match:
            result["prefixes_received"] = int(received_match.group(1))

        if advertised_match:
            result["prefixes_sent"] = int(advertised_match.group(1))

        logger.debug(
            f"Prefixos parseados para {peer_ip}: "
            f"received={result['prefixes_received']}, sent={result['prefixes_sent']}"
        )

    except Exception as e:
        logger.error(f"Erro ao parsear prefixos BGP: {e}")

    return result


def parse_interface_brief(output: str) -> List[Interface]:
    """
    Parseia a saída do comando 'display interface brief'.

    Formato esperado (Huawei NE8000):
    Interface                   PHY   Protocol  InUti OutUti   inErrors  outErrors
    Ethernet0/0/0               up    up        0.01%  0.01%       1337          0
    GigabitEthernet0/7/0(10G)   up    down      4.29% 43.06%          0          0

    Args:
        output: Saída do comando display interface brief

    Returns:
        Lista de objetos Interface
    """
    interfaces = []

    try:
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Pular linhas vazias, cabeçalhos e legendas
            if not line or "Interface" in line or "PHY" in line:
                continue
            if line.startswith("*down") or line.startswith("^down"):
                continue
            if line.startswith("(") or line.startswith("InUti"):
                continue

            # Formato: Nome  PHY  Protocol  InUti  OutUti  inErrors  outErrors
            # Exemplo: Ethernet0/0/0  up  up  0.01%  0.01%  1337  0
            parts = line.split()

            if len(parts) < 3:
                continue

            # Extrair nome da interface (pode ter (10G) no final)
            name_raw = parts[0]
            name = re.sub(r"\(\d+G\)", "", name_raw)  # Remove (10G) se houver

            # Status físico e protocolo
            phy_status = parts[1].lower() if len(parts) > 1 else "unknown"
            protocol_status = parts[2].lower() if len(parts) > 2 else "unknown"

            # Status geral: UP se ambos UP, senão DOWN
            if phy_status == "up" and protocol_status == "up":
                status = "up"
            else:
                status = "down"

            interface = Interface(name=name, status=status, description=None, bandwidth_capacity=0)

            interfaces.append(interface)
            logger.debug(f"Interface parseada (brief): {name} - {status}")

    except Exception as e:
        logger.error(f"Erro ao parsear interface brief: {e}")
        logger.debug(f"Output problemático: {output}")

    return interfaces


def parse_interface_description(output: str) -> List[Interface]:  # noqa: C901
    """
    Parseia a saída do comando 'display interface description'.

    Este comando mostra TODAS as interfaces, incluindo portas SFP down/inativas.

    Formato esperado (Huawei NE8000):
    Interface                     PHY     Protocol Description
    Eth0/0/0                      up      up
    GE0/7/0(10G)                  up      down     P2P - CGNAT - 01
    GE0/7/2(10G)                  down    down

    Args:
        output: Saída do comando display interface description

    Returns:
        Lista de objetos Interface (incluindo interfaces down)
    """
    interfaces = []

    try:
        lines = output.strip().split("\n")

        for line in lines:
            line_stripped = line.strip()

            # Pular linhas vazias
            if not line_stripped:
                continue

            # Pular cabeçalhos e legendas (linhas 1-13 tipicamente)
            if "Interface" in line_stripped and "PHY" in line_stripped:
                continue
            if line_stripped.startswith("---") or line_stripped.startswith("==="):
                continue
            if line_stripped.startswith("(") or line_stripped.startswith("*down"):
                continue
            if "current state" in line_stripped.lower():
                continue

            # Parsear linha de interface
            # Formato: Nome(capacidade)  PHY  Protocol  Description(opcional)
            # Usar split com maxsplit para preservar descrição com espaços
            parts = line_stripped.split(None, 3)  # Split máximo em 4 partes

            if len(parts) < 3:
                continue

            # Extrair nome (remover sufixo de capacidade como (10G))
            name_raw = parts[0]
            name = re.sub(r"\(\d+[GM]\)", "", name_raw)  # Remove (10G), (1G), etc

            # Status físico e protocolo
            phy_status = parts[1].lower()
            protocol_status = parts[2].lower()

            # Descrição (opcional, pode não existir)
            description = parts[3].strip() if len(parts) > 3 else None

            # Status geral: UP apenas se AMBOS up, senão DOWN
            if phy_status == "up" and protocol_status == "up":
                status = "up"
            else:
                status = "down"

            interface = Interface(
                name=name, status=status, description=description, bandwidth_capacity=0
            )

            interfaces.append(interface)
            logger.debug(f"Interface parseada (description): {name} - {status} - {description}")

    except Exception as e:
        logger.error(f"Erro ao parsear interface description: {e}")
        logger.debug(f"Output problemático: {output}")

    return interfaces


def parse_interface(output: str) -> List[Interface]:
    """
    Parseia a saída do comando 'display interface <name>' (detalhado).

    Formato esperado:
    GigabitEthernet0/0/1 current state : UP
    Line protocol current state : UP
    Description: Link to Provider A
    ...

    Args:
        output: Saída do comando display interface <name>

    Returns:
        Lista de objetos Interface (geralmente 1)
    """
    interfaces = []

    try:
        lines = output.strip().split("\n")

        if not lines:
            return interfaces

        # Primeira linha tem o nome e status
        first_line = lines[0]
        name_match = re.match(r"^([A-Za-z0-9\-/\.]+)\s+current state\s*:\s*(\w+)", first_line)

        if not name_match:
            logger.warning(f"Não foi possível parsear primeira linha: {first_line}")
            return interfaces

        name = name_match.group(1)
        status = name_match.group(2).lower()

        # Procurar descrição
        description = None
        for line in lines:
            if "Description" in line:
                desc_match = re.search(r"Description:\s*(.+)", line)
                if desc_match:
                    description = desc_match.group(1).strip()
                break

        interface = Interface(
            name=name, status=status, description=description, bandwidth_capacity=0
        )

        interfaces.append(interface)
        logger.debug(f"Interface parseada: {name} - {status}")

    except Exception as e:
        logger.error(f"Erro ao parsear interface: {e}")
        logger.debug(f"Output problemático: {output}")

    return interfaces


def parse_interface_statistics(output: str, interface_name: str) -> Dict[str, Any]:  # noqa: C901
    """
    Parseia a saída do comando 'display interface <name>'.

    Extrai estatísticas de tráfego, erros e descartes.

    Args:
        output: Saída do comando
        interface_name: Nome da interface

    Returns:
        Dicionário com estatísticas
    """
    stats = {
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

    try:
        # Procurar por input/output rate
        # Exemplo: "Input bandwidth utilization  : 45%"
        #          "Output bandwidth utilization : 30%"
        #          "Input rate: 125000000 bps, 15000 pps"

        input_rate_match = re.search(
            r"Input.*?rate.*?:\s*([\d]+)\s*(?:bps|Bps)", output, re.IGNORECASE
        )
        output_rate_match = re.search(
            r"Output.*?rate.*?:\s*([\d]+)\s*(?:bps|Bps)", output, re.IGNORECASE
        )

        if input_rate_match:
            stats["bandwidth_in_bps"] = int(input_rate_match.group(1))
        if output_rate_match:
            stats["bandwidth_out_bps"] = int(output_rate_match.group(1))

        # Procurar por pacotes por segundo
        input_pps_match = re.search(r"Input.*?(\d+)\s*pps", output, re.IGNORECASE)
        output_pps_match = re.search(r"Output.*?(\d+)\s*pps", output, re.IGNORECASE)

        if input_pps_match:
            stats["packets_in_pps"] = int(input_pps_match.group(1))
        if output_pps_match:
            stats["packets_out_pps"] = int(output_pps_match.group(1))

        # Procurar por erros
        input_errors_match = re.search(r"Input errors:\s*(\d+)", output, re.IGNORECASE)
        output_errors_match = re.search(r"Output errors:\s*(\d+)", output, re.IGNORECASE)

        if input_errors_match:
            stats["errors_in"] = int(input_errors_match.group(1))
        if output_errors_match:
            stats["errors_out"] = int(output_errors_match.group(1))

        # Procurar por descartes
        input_discards_match = re.search(r"Input.*?discard.*?:\s*(\d+)", output, re.IGNORECASE)
        output_discards_match = re.search(r"Output.*?discard.*?:\s*(\d+)", output, re.IGNORECASE)

        if input_discards_match:
            stats["discards_in"] = int(input_discards_match.group(1))
        if output_discards_match:
            stats["discards_out"] = int(output_discards_match.group(1))

        # Procurar bandwidth capacity
        bandwidth_match = re.search(r"BW:\s*(\d+)\s*([KMG]bps)", output, re.IGNORECASE)
        if bandwidth_match:
            value = int(bandwidth_match.group(1))
            unit = bandwidth_match.group(2).upper()
            if "GBPS" in unit or "G" in unit:
                stats["bandwidth_capacity"] = value * 1_000_000_000
            elif "MBPS" in unit or "M" in unit:
                stats["bandwidth_capacity"] = value * 1_000_000
            elif "KBPS" in unit or "K" in unit:
                stats["bandwidth_capacity"] = value * 1_000
            else:
                stats["bandwidth_capacity"] = value

        logger.debug(f"Estatísticas parseadas para {interface_name}: {stats}")

    except Exception as e:
        logger.error(f"Erro ao parsear estatísticas de interface: {e}")

    return stats


def _parse_uptime(uptime_str: str) -> int:
    """
    Converte string de uptime para segundos.

    Formatos suportados:
    - "00:05:23" (HH:MM:SS)
    - "1d00h05m" (days, hours, minutes)
    - "Never"

    Args:
        uptime_str: String de uptime

    Returns:
        Uptime em segundos
    """
    if not uptime_str or uptime_str.lower() == "never":
        return 0

    try:
        # Formato HH:MM:SS
        if ":" in uptime_str:
            parts = uptime_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds

        # Formato 1d00h05m
        days_match = re.search(r"(\d+)d", uptime_str)
        hours_match = re.search(r"(\d+)h", uptime_str)
        minutes_match = re.search(r"(\d+)m", uptime_str)

        total_seconds = 0
        if days_match:
            total_seconds += int(days_match.group(1)) * 86400
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        return total_seconds

    except Exception as e:
        logger.warning(f"Erro ao parsear uptime '{uptime_str}': {e}")
        return 0
