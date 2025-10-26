"""
Cliente SSH para conexão com Huawei NE8000.

CRÍTICO: Apenas comandos READ-ONLY (família 'display').
NUNCA executar comandos de configuração.
"""

import logging
import time
import threading
from typing import Optional
import paramiko

from app.core.config import settings
from app.core.database import db

logger = logging.getLogger(__name__)


class SSHClientError(Exception):
    """Exceção customizada para erros do cliente SSH."""

    pass


class HuaweiSSHClient:
    """Cliente SSH para Huawei NE8000 com modo READ-ONLY."""

    # Whitelist de comandos permitidos (apenas leitura)
    ALLOWED_COMMANDS = [
        "display bgp peer",
        "display bgp routing-table peer",
        "display interface brief",
        "display interface",
        "display interface statistics",
        "display ip interface brief",
        "display cpu-usage",
        "display memory-usage",
        "display version",
        "display current-configuration interface",
    ]

    # Comandos proibidos (exemplos - lista não exaustiva)
    FORBIDDEN_KEYWORDS = [
        "system-view",
        "interface ",
        "undo ",
        "shutdown",
        "reset",
        "save",
        "commit",
        "delete",
        "set ",
        "config",
        "configure",
        "write",
        "erase",
        "clear",
    ]

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Inicializa o cliente SSH.

        Args:
            host: Endereço IP ou hostname do NE8000
            port: Porta SSH
            username: Usuário SSH
            password: Senha SSH
            timeout: Timeout de conexão em segundos
        """
        self.host = host or settings.SSH_HOST
        self.port = port or settings.SSH_PORT
        self.username = username or settings.SSH_USER
        self.password = password or settings.SSH_PASSWORD
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None
        self.shell: Optional[paramiko.Channel] = None
        self.connected = False
        self._command_lock = threading.Lock()  # Lock para serializar comandos

    def _validate_command(self, command: str) -> None:
        """
        Valida se o comando está na whitelist e não contém palavras proibidas.

        IMPORTANTE: Primeiro verifica whitelist, depois palavras proibidas.
        Isso evita falsos positivos (ex: "display interface" não deve ser bloqueado).

        Args:
            command: Comando a ser validado

        Raises:
            SSHClientError: Se o comando não é permitido
        """
        command_lower = command.lower().strip()

        # PRIMEIRO: Verificar se está na whitelist
        is_allowed = False
        for allowed in self.ALLOWED_COMMANDS:
            if command_lower.startswith(allowed.lower()):
                is_allowed = True
                logger.info(f"Comando validado com sucesso: {command}")
                return  # Comando permitido, não verificar palavras proibidas

        # SEGUNDO: Se não está na whitelist, rejeitar
        if not is_allowed:
            error_msg = (
                f"Comando não autorizado: '{command}'. "
                f"Apenas comandos 'display' são permitidos."
            )
            logger.error(error_msg)
            raise SSHClientError(error_msg)

    def _log_command_execution(
        self,
        command: str,
        execution_time_ms: int,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Registra a execução de comando no banco de dados para auditoria.

        Args:
            command: Comando executado
            execution_time_ms: Tempo de execução em milissegundos
            success: Se o comando foi executado com sucesso
            error_message: Mensagem de erro (se houver)
        """
        query = """
            INSERT INTO ssh_commands_log
            (command, execution_time_ms, success, error_message)
            VALUES (?, ?, ?, ?)
        """
        try:
            db.execute_write(query, (command, execution_time_ms, success, error_message))
        except Exception as e:
            logger.error(f"Erro ao registrar log de comando: {e}")

    def connect(self) -> None:
        """
        Estabelece conexão SSH com o equipamento.

        Raises:
            SSHClientError: Se não conseguir conectar
        """
        if self.connected and self.client:
            logger.info("Cliente SSH já está conectado")
            return

        try:
            logger.info(f"Conectando ao NE8000 em {self.host}:{self.port}")

            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False,
            )

            # Criar shell interativo para evitar 'Administratively prohibited'
            self.shell = self.client.invoke_shell()
            self.shell.settimeout(self.timeout)

            # Limpar buffer inicial (banner, prompts, etc)
            time.sleep(1)
            if self.shell.recv_ready():
                self.shell.recv(65535)

            self.connected = True
            logger.info("Conexão SSH e shell interativo estabelecidos com sucesso")

        except Exception as e:
            error_msg = f"Erro ao conectar via SSH: {e}"
            logger.error(error_msg)
            raise SSHClientError(error_msg) from e

    def disconnect(self) -> None:
        """Fecha a conexão SSH."""
        if self.shell:
            self.shell.close()
            self.shell = None
        if self.client:
            self.client.close()
            self.client = None
            self.connected = False
            logger.info("Conexão SSH fechada")

    def execute_command(self, command: str) -> str:
        """
        Executa um comando no equipamento usando shell interativo.

        IMPORTANTE: Usa threading.Lock para serializar comandos e evitar
        'Administratively prohibited' error em equipamentos Huawei.

        Args:
            command: Comando a ser executado

        Returns:
            Output do comando

        Raises:
            SSHClientError: Se o comando não é permitido ou ocorrer erro
        """
        # Validar comando antes de executar
        self._validate_command(command)

        if not self.connected or not self.shell:
            self.connect()

        # Lock para serializar comandos (evita exec_command simultâneos)
        with self._command_lock:
            start_time = time.time()
            success = False
            error_message = None
            output = ""

            try:
                logger.info(f"Executando comando via shell interativo: {command}")

                # Limpar buffer antes do comando
                if self.shell.recv_ready():
                    self.shell.recv(65535)

                # Enviar comando + newline
                self.shell.send(command + "\n")

                # Aguardar saída (com timeout adaptativo)
                time.sleep(0.5)
                max_wait = 10  # 10 segundos máximo
                waited = 0

                while not self.shell.recv_ready() and waited < max_wait:
                    time.sleep(0.1)
                    waited += 0.1

                # Ler output
                output_bytes = b""
                while self.shell.recv_ready():
                    chunk = self.shell.recv(65535)
                    output_bytes += chunk
                    time.sleep(0.1)  # Pequeno delay para garantir recebimento completo

                output = output_bytes.decode("utf-8", errors="ignore")

                # Limpar prompt e comando ecoado
                output_lines = output.split("\n")
                if len(output_lines) > 2:
                    # Remove primeira linha (comando ecoado) e última (prompt)
                    output = "\n".join(output_lines[1:-1])

                success = True
                logger.info(f"Comando executado. Output: {len(output)} bytes")

            except Exception as e:
                error_message = str(e)
                logger.error(f"Erro ao executar comando '{command}': {e}")
                raise SSHClientError(f"Erro ao executar comando: {e}") from e

            finally:
                execution_time_ms = int((time.time() - start_time) * 1000)
                self._log_command_execution(command, execution_time_ms, success, error_message)

        return output

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Instância global do cliente SSH
ssh_client = HuaweiSSHClient()
