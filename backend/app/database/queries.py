from collections.abc import Mapping, Sequence
from typing import Any

from psycopg import sql
from psycopg.rows import dict_row

from app.database.connection import get_connection


def list_records(table: str, columns: Sequence[str]) -> list[dict[str, Any]]:
    query = sql.SQL("SELECT {columns} FROM {table} ORDER BY id").format(
        columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
        table=sql.Identifier(table),
    )
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def get_record(
    table: str, columns: Sequence[str], record_id: int
) -> dict[str, Any] | None:
    query = sql.SQL("SELECT {columns} FROM {table} WHERE id = %s").format(
        columns=sql.SQL(", ").join(map(sql.Identifier, columns)),
        table=sql.Identifier(table),
    )
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, (record_id,))
            return cursor.fetchone()


def create_record(
    table: str, columns: Sequence[str], values: Mapping[str, Any]
) -> dict[str, Any]:
    insert_columns = sql.SQL(", ").join(map(sql.Identifier, values))
    placeholders = ", ".join("%s" for _ in values)
    returned_columns = sql.SQL(", ").join(map(sql.Identifier, columns))
    query = sql.SQL(
        "INSERT INTO {table} ({insert_columns}) VALUES ({placeholders}) RETURNING {columns}"
    ).format(
        table=sql.Identifier(table),
        insert_columns=insert_columns,
        placeholders=sql.SQL(placeholders),
        columns=returned_columns,
    )
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, tuple(values.values()))
            record = cursor.fetchone()
            if record is None:
                raise RuntimeError("Insert did not return the created record")
            connection.commit()
            return record


def update_record(
    table: str,
    columns: Sequence[str],
    record_id: int,
    values: Mapping[str, Any],
) -> dict[str, Any] | None:
    assignments = sql.SQL(", ").join(
        sql.SQL("{column} = %s").format(column=sql.Identifier(column))
        for column in values
    )
    returned_columns = sql.SQL(", ").join(map(sql.Identifier, columns))
    query = sql.SQL(
        "UPDATE {table} SET {assignments} WHERE id = %s RETURNING {columns}"
    ).format(
        table=sql.Identifier(table),
        assignments=assignments,
        columns=returned_columns,
    )
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, (*values.values(), record_id))
            record = cursor.fetchone()
            connection.commit()
            return record


def delete_record(table: str, columns: Sequence[str], record_id: int) -> bool:
    query = sql.SQL("DELETE FROM {table} WHERE id = %s").format(
        table=sql.Identifier(table)
    )
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (record_id,))
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
