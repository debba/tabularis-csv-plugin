# Changelog

## [1.0.0] - 2026-02-25

### Added

- Initial release.
- Load any folder of `.csv` / `.tsv` files as a Tabularis database.
- Auto-delimiter detection (`,` `;` `\t` `|`) via `csv.Sniffer`.
- Full SQL query execution via in-memory SQLite.
- Schema inspection: `get_tables`, `get_columns`.
- Batch methods for ER diagram support: `get_schema_snapshot`, `get_all_columns_batch`.
- `sync.sh` for local development installs.
