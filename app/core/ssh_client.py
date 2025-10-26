"""
Cliente SSH para conexão com Huawei NE8000.

CRÍTICO: Apenas comandos READ-ONLY (família 'display').
NUNCA executar comandos de configuração.
"""
import logging
import time
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
        "display interface",
        "display interface statistics",
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
        timeout: int = 30
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
        self.connected = False

    def _validate_command(self, command: str) -> None:
        """
        Valida se o comando está na whitelist e não contém palavras proibidas.

        Args:
            command: Comando a ser validado

        Raises:
            SSHClientError: Se o comando não é permitido
        """
        command_lower = command.lower().strip()

        # Verificar se contém palavras proibidas
        for forbidden in self.FORBIDDEN_KEYWORDS:
            if forbidden.lower() in command_lower:
                error_msg = (
                    f"COMANDO PROIBIDO detectado: '{command}' "
                    f"contém palavra-chave proibida: '{forbidden}'"
                )
                logger.error(error_msg)
                raise SSHClientError(error_msg)

        # Verificar se está na whitelist
        is_allowed = False
        for allowed in self.ALLOWED_COMMANDS:
            if command_lower.startswith(allowed.lower()):
                is_allowed = True
                break

        if not is_allowed:
            error_msg = (
                f"Comando não autorizado: '{command}'. "
                f"Apenas comandos 'display' são permitidos."
            )
            logger.error(error_msg)
            raise SSHClientError(error_msg)

        logger.info(f"Comando validado com sucesso: {command}")

    def _log_command_execution(
        self,
        command: str,
        execution_time_ms: int,
        success: bool,
        error_message: Optional[str] = None
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
                allow_agent=False
            )

            self.connected = True
            logger.info("Conexão SSH estabelecida com sucesso")

        except Exception as e:
            error_msg = f"Erro ao conectar via SSH: {e}"
            logger.error(error_msg)
            raise SSHClientError(error_msg) from e

    def disconnect(self) -> None:
        """Fecha a conexão SSH."""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Conexão SSH fechada")

    def execute_command(self, command: str) -> str:
        """
        Executa um comando no equipamento (apenas comandos da whitelist).

        Args:
            command: Comando a ser executado

        Returns:
            Output do comando

        Raises:
            SSHClientError: Se o comando não é permitido ou ocorrer erro
        """
        # Validar comando antes de executar
        self._validate_command(command)

        if not self.connected or not self.client:
            self.connect()

        start_time = time.time()
        success = False
        error_message = None
        output = ""

        try:
            logger.info(f"Executando comando: {command}")

            stdin, stdout, stderr = self.client.exec_command(
                command,
                timeout=self.timeout
            )

            output = stdout.read().decode("utf-8")
            error_output = stderr.read().decode("utf-8")

            if error_output:
                logger.warning(f"Comando gerou erro: {error_output}")
                error_message = error_output

            success = True
            logger.info(f"Comando executado com sucesso. Output: {len(output)} bytes")

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
