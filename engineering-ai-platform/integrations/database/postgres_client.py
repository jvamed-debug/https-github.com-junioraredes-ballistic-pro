"""PostgreSQL Client — integração com PostgreSQL e pgvector."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectionConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "eap"
    user: str = "postgres"
    password: str = ""
    ssl: bool = False

    @property
    def dsn(self) -> str:
        scheme = "postgresql+asyncpg" if self.ssl else "postgresql"
        return f"{scheme}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class QueryResult:
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    columns: list[str] = field(default_factory=list)


class PostgresClient:
    """Cliente para PostgreSQL com suporte a pgvector."""

    def __init__(self, config: ConnectionConfig | None = None) -> None:
        self._config = config or ConnectionConfig()
        self._pool: Any = None

    async def connect(self) -> None:
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                host=self._config.host,
                port=self._config.port,
                database=self._config.database,
                user=self._config.user,
                password=self._config.password,
                min_size=2,
                max_size=10,
            )
        except ImportError:
            raise ImportError("asyncpg is required: pip install asyncpg")

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def execute(self, query: str, *args: Any) -> QueryResult:
        if not self._pool:
            raise RuntimeError("Not connected — call connect() first")
        async with self._pool.acquire() as conn:
            result = await conn.fetch(query, *args)
            rows = [dict(row) for row in result]
            columns = list(rows[0].keys()) if rows else []
            return QueryResult(rows=rows, row_count=len(rows), columns=columns)

    async def execute_many(self, query: str, args_list: list[tuple[Any, ...]]) -> int:
        if not self._pool:
            raise RuntimeError("Not connected — call connect() first")
        async with self._pool.acquire() as conn:
            await conn.executemany(query, args_list)
            return len(args_list)

    async def setup_pgvector(self) -> None:
        if not self._pool:
            raise RuntimeError("Not connected — call connect() first")
        async with self._pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

    async def create_vector_table(self, table_name: str, dimension: int = 384) -> None:
        if not self._pool:
            raise RuntimeError("Not connected — call connect() first")
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    embedding vector({dimension}),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_embedding
                ON {table_name} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)

    async def vector_search(
        self, table_name: str, query_vector: list[float], limit: int = 10
    ) -> list[dict[str, Any]]:
        if not self._pool:
            raise RuntimeError("Not connected — call connect() first")
        vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"
        async with self._pool.acquire() as conn:
            result = await conn.fetch(f"""
                SELECT id, content, metadata, 1 - (embedding <=> $1::vector) AS similarity
                FROM {table_name}
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """, vec_str, limit)
            return [dict(row) for row in result]

    async def health_check(self) -> bool:
        try:
            if not self._pool:
                return False
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
                return True
        except Exception:
            return False
