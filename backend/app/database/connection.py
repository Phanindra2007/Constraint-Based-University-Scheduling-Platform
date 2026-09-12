from contextlib import AbstractContextManager

from psycopg import Connection
from psycopg_pool import ConnectionPool
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

pool = ConnectionPool(
    conninfo=(
        f"host={DB_HOST} "
        f"port={DB_PORT} "
        f"dbname={DB_NAME} "
        f"user={DB_USER} "
        f"password={DB_PASSWORD}"
    ),
    min_size=2,
    max_size=10,
)


def close_pool():
    """Close the connection pool."""
    pool.close()


def get_connection() -> AbstractContextManager[Connection]:
    """Borrow a connection from the pool and return it when finished."""
    return pool.connection()
