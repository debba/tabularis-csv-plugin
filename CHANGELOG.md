# Changelog

## [1.0.1] - 2026-02-25

### Fixed

- `manifest.json`: renamed `has_length` → `requires_length` / `requires_precision` to match the Tabularis `DataTypeInfo` struct. Previously the plugin silently failed to register after installation.

## [1.0.0] - 2026-02-25

### Added

- Initial release.
- Load any folder of `.csv` / `.tsv` files as a Tabularis database.
- Auto-delimiter detection (`,` `;` `\t` `|`) via `csv.Sniffer`.
- Full SQL query execution via in-memory SQLite.
- Schema inspection: `get_tables`, `get_columns`.
- Batch methods for ER diagram support: `get_schema_snapshot`, `get_all_columns_batch`.
- `sync.sh` for local development installs.
