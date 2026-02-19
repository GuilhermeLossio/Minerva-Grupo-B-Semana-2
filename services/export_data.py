from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any, Mapping, Sequence

import pandas as pd

DEFAULT_ENCODING = "utf-8"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str, *, label: str) -> str:
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid {label} identifier: {name!r}")
    return name


def _quote_identifier(name: str) -> str:
    return f'"{name}"'


def _qualified_table_name(table: str, schema: str | None = None) -> str:
    if schema:
        schema = _validate_identifier(schema, label="schema")
        table = _validate_identifier(table, label="table")
        return f'{_quote_identifier(schema)}.{_quote_identifier(table)}'

    if "." in table:
        parts = table.split(".")
        safe_parts = [_quote_identifier(_validate_identifier(p, label="table part")) for p in parts]
        return ".".join(safe_parts)

    table = _validate_identifier(table, label="table")
    return _quote_identifier(table)


def dataframe_to_csv_bytes(
    df: pd.DataFrame, *, encoding: str = DEFAULT_ENCODING, include_index: bool = False
) -> bytes:
    return df.to_csv(index=include_index).encode(encoding)


def build_csv_extract(
    df: pd.DataFrame | None,
    *,
    selected_columns: Sequence[str] | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()

    active_columns = list(selected_columns) if selected_columns else list(df.columns)
    work_df = df[active_columns].copy()

    if max_rows is None or max_rows <= 0:
        return work_df

    return work_df.head(max_rows)


def export_csv_extract_to_csv_bytes(
    df: pd.DataFrame | None,
    *,
    selected_columns: Sequence[str] | None = None,
    max_rows: int | None = None,
    encoding: str = DEFAULT_ENCODING,
    include_index: bool = False,
) -> bytes:
    extract_df = build_csv_extract(
        df, selected_columns=selected_columns, max_rows=max_rows
    )
    return dataframe_to_csv_bytes(extract_df, encoding=encoding, include_index=include_index)


def export_csv_extract_to_json_bytes(
    df: pd.DataFrame | None,
    *,
    selected_columns: Sequence[str] | None = None,
    max_rows: int | None = None,
    encoding: str = DEFAULT_ENCODING,
    indent: int = 2,
) -> bytes:
    extract_df = build_csv_extract(
        df, selected_columns=selected_columns, max_rows=max_rows
    )
    payload = extract_df.to_dict(orient="records")
    text = json.dumps(payload, ensure_ascii=False, indent=indent)
    return text.encode(encoding)


def export_session_to_csv(
    session_state: Mapping[str, Any],
    *,
    encoding: str = DEFAULT_ENCODING,
    include_meta: bool = True,
    include_index: bool = False,
) -> bytes:
    """Export session messages to a CSV payload."""
    messages = session_state.get("messages", []) or []
    rows: list[dict[str, Any]] = []

    system_prompt = session_state.get("system_prompt", "") if include_meta else ""
    csv_meta = session_state.get("csv_meta", {}) if include_meta else {}

    for idx, message in enumerate(messages):
        row = {
            "message_index": idx,
            "role": message.get("role", ""),
            "content": message.get("content", ""),
        }

        if include_meta:
            row["system_prompt"] = system_prompt
            row["csv_rows"] = csv_meta.get("rows")
            row["csv_columns_count"] = (
                len(csv_meta.get("columns", [])) if isinstance(csv_meta.get("columns", []), list) else None
            )
        rows.append(row)

    df = pd.DataFrame(rows)
    return dataframe_to_csv_bytes(df, encoding=encoding, include_index=include_index)


def export_db_table_to_csv(
    conn: Any,
    table: str,
    *,
    schema: str | None = None,
    columns: Sequence[str] | None = None,
    where: str | None = None,
    params: Mapping[str, Any] | Sequence[Any] | None = None,
    encoding: str = DEFAULT_ENCODING,
    include_index: bool = False,
) -> bytes:
    """Export a database table to CSV using a DB-API connection or SQLAlchemy engine."""
    table_ref = _qualified_table_name(table, schema=schema)
    if columns:
        safe_cols = [_quote_identifier(_validate_identifier(c, label="column")) for c in columns]
        select_cols = ", ".join(safe_cols)
    else:
        select_cols = "*"

    query = f"SELECT {select_cols} FROM {table_ref}"
    if where:
        query = f"{query} WHERE {where}"

    df = pd.read_sql_query(query, conn, params=params)
    return dataframe_to_csv_bytes(df, encoding=encoding, include_index=include_index)


def export_db_table_to_file(
    conn: Any,
    table: str,
    output_path: str | Path,
    *,
    schema: str | None = None,
    columns: Sequence[str] | None = None,
    where: str | None = None,
    params: Mapping[str, Any] | Sequence[Any] | None = None,
    encoding: str = DEFAULT_ENCODING,
    include_index: bool = False,
) -> Path:
    """Export a database table to a CSV file and return the file path."""
    csv_bytes = export_db_table_to_csv(
        conn,
        table,
        schema=schema,
        columns=columns,
        where=where,
        params=params,
        encoding=encoding,
        include_index=include_index,
    )
    path = Path(output_path)
    path.write_bytes(csv_bytes)
    return path
