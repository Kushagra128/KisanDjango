# SQL Migration Files

This folder contains SQL scripts for database migrations:

- **FIX_DATABASE.sql** - Add embedding column to pesti_comp
- **RENAME_TABLE.sql** - Rename solutions table to pesti_comp
- **CLEANUP_OLD_TABLES.sql** - Remove duplicate/old tables

## Usage

Connect to PostgreSQL and run:
```bash
psql -U querymind -d Kisan_AI -f sql/FIX_DATABASE.sql
```

Or use the Python scripts in `scripts/` folder which execute these automatically.
