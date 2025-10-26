"""
Gerenciamento de banco de dados SQLite com queries SQL diretas.

IMPORTANTE: Não usar ORM (SQLAlchemy). Apenas SQL puro.
SEMPRE usar 'with db.get_connection()' para transações.
"""
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Gerenciador de banco de dados SQLite."""

    def __init__(self, db_path: str):
        """
        Inicializa o gerenciador de banco de dados.

        Args:
            db_path: Caminho para o arquivo do banco SQLite
        """
        self.db_path = db_path
        self._ensure_database_exists()
        self._initialize_schema()

    def _ensure_database_exists(self) -> None:
        """Garante que o diretório do banco de dados existe."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Banco de dados configurado em: {self.db_path}")

    def _initialize_schema(self) -> None:
        """Inicializa o schema do banco de dados."""
        schema_path = Path(__file__).parent.parent.parent / "schema.sql"

        if not schema_path.exists():
            logger.error(f"Arquivo schema.sql não encontrado em: {schema_path}")
            raise FileNotFoundError(f"Schema SQL não encontrado: {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()

        logger.info("Schema do banco de dados inicializado com sucesso")

    @contextmanager
    def get_connection(self):
        """
        Context manager para obter conexão com o banco.

        Uso:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
                conn.commit()

        Yields:
            sqlite3.Connection: Conexão com o banco de dados
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro na transação do banco de dados: {e}")
            raise
        finally:
            conn.close()

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Executa uma query SELECT e retorna os resultados.

        Args:
            query: Query SQL SELECT
            params: Parâmetros da query (opcional)

        Returns:
            Lista de dicionários com os resultados

        Note:
            NÃO usar este método dentro de 'with get_connection()'.
            Use o cursor diretamente nesse caso.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results

    def execute_single(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executa uma query SELECT e retorna apenas o primeiro resultado.

        Args:
            query: Query SQL SELECT
            params: Parâmetros da query (opcional)

        Returns:
            Dicionário com o resultado ou None

        Note:
            NÃO usar este método dentro de 'with get_connection()'.
            Use o cursor diretamente nesse caso.
        """
        results = self.execute_query(query, params)
        return results[0] if results else None

    def execute_write(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> int:
        """
        Executa uma query de escrita (INSERT, UPDATE, DELETE).

        Args:
            query: Query SQL de escrita
            params: Parâmetros da query (opcional)

        Returns:
            ID da última linha inserida (para INSERT) ou número de linhas afetadas

        Note:
            NÃO usar este método dentro de 'with get_connection()'.
            Use o cursor diretamente nesse caso.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid > 0 else cursor.rowcount

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """
        Executa múltiplas queries de escrita em batch.

        Args:
            query: Query SQL de escrita
            params_list: Lista de tuplas com parâmetros

        Returns:
            Número total de linhas afetadas

        Note:
            NÃO usar este método dentro de 'with get_connection()'.
            Use o cursor diretamente nesse caso.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount


# Instância global do banco de dados
db = Database(settings.DB_PATH)
