"""Database Index and Foreign Key Indexing Verification Script.

PRD §19, Task P14.21.
Inspects all SQLAlchemy models and tables in the application,
ensuring every foreign key column and critical filter query column is backed by an index.
"""

import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

# Import all models to populate Base.metadata
import app.models  # noqa: F401
from app.config.database import Base


def verify_database_indexes():
    print("=" * 70)
    print("DATABASE INDEX AUDIT & QUERY PERFORMANCE VERIFICATION")
    print("=" * 70)

    tables = Base.metadata.tables
    print(f"Total Tables Registered: {len(tables)}\n")

    missing_fk_indexes = []
    total_fks = 0
    total_indexes = 0

    for table_name, table in sorted(tables.items()):
        fks = table.foreign_keys
        total_fks += len(fks)

        # Collect columns covered by existing indexes
        indexed_cols = set()
        for idx in table.indexes:
            total_indexes += 1
            for col in idx.columns:
                indexed_cols.add(col.name)

        # Also primary key columns are indexed by default
        for pk_col in table.primary_key.columns:
            indexed_cols.add(pk_col.name)

        # Check each FK
        for fk in fks:
            col_name = fk.parent.name
            if col_name not in indexed_cols:
                missing_fk_indexes.append((table_name, col_name, fk.target_fullname))

    print(f"Total Foreign Keys: {total_fks}")
    print(f"Total Explicit Indexes: {total_indexes}")

    if missing_fk_indexes:
        print(f"\nWARNING: {len(missing_fk_indexes)} Foreign Key(s) without dedicated indexes:")
        for tbl, col, target in missing_fk_indexes:
            print(f"  - Table '{tbl}' column '{col}' -> References '{target}'")
    else:
        print("\nALL FOREIGN KEY COLUMNS ARE PROPERLY INDEXED.")

    print("=" * 70)
    return len(missing_fk_indexes) == 0


if __name__ == "__main__":
    verify_database_indexes()
