#!/usr/bin/env python3
"""
tabularis-csv-plugin
--------------------
Turns a folder of .csv / .tsv files into a queryable database inside Tabularis.
Each file becomes a table. Full SQL via in-memory SQLite.

Zero dependencies — Python 3.8+ standard library only.
"""

import csv
import json
import sqlite3
import sys
import time
from pathlib import Path

# Per-session state: one SQLite connection per folder, reused across calls.
_conn: sqlite3.Connection | None = None
_loaded_folder: str | None = None


# ── CSV loading ──────────────────────────────────────────────────────────────

def _sniff_delimiter(path: Path) -> str:
    """Auto-detect the delimiter by sampling the first 4 KB of the file."""
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        sample = f.read(4096)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def _load_folder(folder: str) -> sqlite3.Connection:
    """Read every .csv / .tsv in folder into a fresh in-memory SQLite DB."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    for path in sorted(Path(folder).glob("*")):
        if path.suffix.lower() not in {".csv", ".tsv"}:
            continue

        table = path.stem
        delimiter = "\t" if path.suffix.lower() == ".tsv" else _sniff_delimiter(path)

        with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            try:
                raw_headers = next(reader)
            except StopIteration:
                continue  # skip empty files

            headers = [h.strip() for h in raw_headers]
            quoted  = [f'"{h}"' for h in headers]
            cols_ddl = ", ".join(f"{q} TEXT" for q in quoted)

            conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols_ddl})')
            conn.executemany(
                f'INSERT INTO "{table}" VALUES ({", ".join("?" * len(headers))})',
                (
                    [c.strip() for c in row]
                    for row in reader
                    if len(row) == len(headers)
                ),
            )

        print(f"[csv-plugin] loaded: {path.name} → table '{table}'", file=sys.stderr)

    conn.commit()
    return conn


def _ensure_loaded(folder: str) -> sqlite3.Connection:
    global _conn, _loaded_folder
    if _conn is None or _loaded_folder != folder:
        _conn = _load_folder(folder)
        _loaded_folder = folder
    return _conn


def _folder(params: dict) -> str:
    return params.get("params", {}).get("database", "")


# ── column shape (reused in several methods) ─────────────────────────────────

def _pragma_columns(db: sqlite3.Connection, table: str) -> list:
    cur = db.execute(f'PRAGMA table_info("{table}")')
    return [
        {
            "name": row["name"],
            "data_type": "TEXT",
            "is_nullable": True,
            "column_default": None,
            "is_primary_key": bool(row["pk"]),
            "is_auto_increment": False,
            "comment": None,
        }
        for row in cur
    ]


# ── method dispatch ───────────────────────────────────────────────────────────

def handle(method: str, params: dict) -> object:
    folder = _folder(params)

    # ── connection ───────────────────────────────────────────────────────────
    if method == "test_connection":
        path = Path(folder)
        if not path.is_dir():
            raise ValueError(f"Not a directory: {folder!r}")
        files = [p for p in path.iterdir() if p.suffix.lower() in {".csv", ".tsv"}]
        if not files:
            raise ValueError(f"No .csv / .tsv files found in: {folder!r}")
        _ensure_loaded(folder)
        return {"success": True}

    db = _ensure_loaded(folder)

    # ── schema discovery ─────────────────────────────────────────────────────
    if method == "get_databases":
        return [Path(folder).name]

    if method in ("get_schemas", "get_foreign_keys", "get_indexes",
                  "get_views", "get_routines"):
        return []

    if method == "get_tables":
        cur = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [{"name": row["name"], "schema": None, "comment": None} for row in cur]

    if method == "get_columns":
        return _pragma_columns(db, params.get("table", ""))

    # ── batch / ER diagram ───────────────────────────────────────────────────
    if method == "get_schema_snapshot":
        cur = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [{"name": r["name"], "schema": None, "comment": None} for r in cur]
        return {
            "tables": tables,
            "columns":      {t["name"]: _pragma_columns(db, t["name"]) for t in tables},
            "foreign_keys": {t["name"]: [] for t in tables},
        }

    if method == "get_all_columns_batch":
        return {t: _pragma_columns(db, t) for t in params.get("tables", [])}

    if method == "get_all_foreign_keys_batch":
        return {t: [] for t in params.get("tables", [])}

    # ── query execution ──────────────────────────────────────────────────────
    if method == "execute_query":
        query     = params.get("query", "").strip()
        page      = max(1, int(params.get("page", 1)))
        page_size = max(1, int(params.get("page_size", 100)))

        t0  = time.monotonic()
        cur = db.execute(query)
        all_rows = cur.fetchall()
        elapsed  = int((time.monotonic() - t0) * 1000)

        col_names = [d[0] for d in (cur.description or [])]
        offset    = (page - 1) * page_size

        return {
            "columns":          col_names,
            "rows":             [list(r) for r in all_rows[offset : offset + page_size]],
            "total_count":      len(all_rows),
            "execution_time_ms": elapsed,
        }

    raise NotImplementedError(method)


# ── JSON-RPC loop ─────────────────────────────────────────────────────────────

def _ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}

def _err(rid, code: int, msg: str):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}


def main():
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue

        try:
            req = json.loads(raw)
        except json.JSONDecodeError as e:
            print(json.dumps(_err(None, -32700, str(e))), flush=True)
            continue

        rid    = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        try:
            out = _ok(rid, handle(method, params))
        except NotImplementedError as e:
            out = _err(rid, -32601, f"Method not found: {e}")
        except Exception as e:
            print(f"[csv-plugin] error in '{method}': {e}", file=sys.stderr)
            out = _err(rid, -32603, str(e))

        print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
