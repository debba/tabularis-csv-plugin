<div align="center">
  <img src="https://raw.githubusercontent.com/debba/tabularis/main/public/logo-sm.png" width="120" height="120" />
</div>

# tabularis-csv-plugin

<p align="center">

![](https://img.shields.io/github/release/debba/tabularis-csv-plugin.svg?style=flat)
![](https://img.shields.io/github/downloads/debba/tabularis-csv-plugin/total.svg?style=flat)
![Build & Release](https://github.com/debba/tabularis-csv-plugin/workflows/Release/badge.svg)
[![Discord](https://img.shields.io/discord/1470772941296894128?color=5865F2&logo=discord&logoColor=white)](https://discord.gg/YrZPHAwMSG)

</p>

A CSV/TSV plugin for [Tabularis](https://github.com/debba/tabularis), the lightweight database management tool.

This plugin turns a **folder of `.csv` or `.tsv` files into a queryable database**. Each file becomes a table. Full SQL support via an in-memory SQLite engine — `JOIN` across files, `GROUP BY`, window functions, CTEs.

**Zero dependencies** — pure Python 3.8+ standard library. No `pip install`.

**Discord** - [Join our discord server](https://discord.gg/YrZPHAwMSG) and chat with the maintainers.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Automatic (via Tabularis)](#automatic-via-tabularis)
  - [Manual Installation](#manual-installation)
- [How It Works](#how-it-works)
- [Supported Operations](#supported-operations)
- [Development](#development)
- [Changelog](#changelog)
- [License](#license)

## Features

- **Any folder, instantly** — point Tabularis at any directory and start querying.
- **Auto-delimiter detection** — automatically detects `,` `;` `\t` `|` separators via `csv.Sniffer`.
- **Full SQL** — uses SQLite as the query engine: `JOIN`, `GROUP BY`, subqueries, CTEs, window functions.
- **Schema Inspection** — browse tables and columns in the sidebar explorer.
- **ER Diagram** — visualize relationships across your CSV files.
- **SQL Execution** — run any query with automatic pagination.
- **Zero dependencies** — ships as a single Python file with no external packages.
- **Cross-platform** — works on Linux, macOS, and Windows wherever Python 3.8+ is installed.

## Installation

### Automatic (via Tabularis)

Open **Settings → Available Plugins** in Tabularis and install **CSV Folder** from the plugin registry.

### Manual Installation

1. Download the latest `csv-plugin.zip` from the [Releases page](https://github.com/debba/tabularis-csv-plugin/releases).
2. Extract the archive.
3. Copy `plugin.py` and `manifest.json` into the Tabularis plugins directory:

| OS | Plugins Directory |
|---|---|
| **Linux** | `~/.local/share/tabularis/plugins/csv/` |
| **macOS** | `~/Library/Application Support/com.debba.tabularis/plugins/csv/` |
| **Windows** | `%APPDATA%\com.debba.tabularis\plugins\csv\` |

4. Make the plugin executable (Linux/macOS):

```bash
chmod +x ~/.local/share/tabularis/plugins/csv/plugin.py
```

5. Restart Tabularis.

Python 3.8 or newer must be available as `python3` in your `PATH`.

## How It Works

The plugin is a single Python script that communicates with Tabularis through **JSON-RPC 2.0 over stdio**:

1. Tabularis spawns `plugin.py` as a child process.
2. Requests are sent as newline-delimited JSON-RPC messages to the plugin's `stdin`.
3. Responses are written to `stdout` in the same format.

On first connection, the plugin scans the target folder, loads every `.csv` / `.tsv` file into an **in-memory SQLite database**, and keeps it alive for the entire session. SQLite handles all query execution.

All debug output is written to `stderr` and appears in Tabularis's log viewer — `stdout` is reserved exclusively for JSON-RPC responses.

## Supported Operations

| Method | Description |
|---|---|
| `test_connection` | Verify folder exists and contains CSV/TSV files |
| `get_databases` | Returns the folder name as the database name |
| `get_tables` | List all CSV/TSV files as tables |
| `get_columns` | Get column names for a table |
| `execute_query` | Execute SQL with pagination support |
| `get_schema_snapshot` | Full schema dump in one call (used for ER diagrams) |
| `get_all_columns_batch` | All columns for all tables in one call |
| `get_all_foreign_keys_batch` | Returns empty (no FK constraints in CSV) |

## Development

### Testing the Plugin

Test the plugin directly from your shell without opening Tabularis:

```bash
chmod +x plugin.py

echo '{"jsonrpc":"2.0","method":"test_connection","params":{"params":{"driver":"csv","database":"/path/to/example","host":null,"port":null,"username":null,"password":null,"ssl_mode":null}},"id":1}' \
  | python3 plugin.py
```

### Install Locally

A convenience script is provided to copy the plugin directly into your Tabularis plugins folder:

```bash
./sync.sh
```

### Try the example dataset

The `example/` folder contains three related CSV files (users, orders, products):

```bash
./sync.sh
# In Tabularis, connect to the absolute path of the example/ folder
```

Then try in the SQL editor:

```sql
SELECT u.name, SUM(CAST(p.price AS REAL) * CAST(o.quantity AS INTEGER)) AS total_spent
FROM orders o
JOIN users u    ON o.user_id    = u.id
JOIN products p ON o.product_id = p.id
GROUP BY u.name
ORDER BY total_spent DESC;
```

### Tech Stack

- **Language:** Python 3.8+ (standard library only)
- **Query engine:** SQLite (via `sqlite3` stdlib module)
- **Protocol:** JSON-RPC 2.0 over stdio

## [Changelog](./CHANGELOG.md)

## License

Apache License 2.0
