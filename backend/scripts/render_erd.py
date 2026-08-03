"""Render the ER diagram from a migrated database to docs/data-model.svg.

Reflects the live schema (tables, columns, types, keys, indexes) so the diagram
matches exactly what the migrations produce. Point DATABASE_URL at any database
migrated to head — e.g. a throwaway Postgres used for migration verification:

    docker run -d --name erd -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=mirai -p 55432:5432 postgres:17
    DATABASE_URL=postgresql+pg8000://postgres:pw@localhost:55432/mirai uv run alembic upgrade head
    DATABASE_URL=postgresql+pg8000://postgres:pw@localhost:55432/mirai \
        uv run --with sqlalchemy_schemadisplay --with pydot python scripts/render_erd.py

Requires the Graphviz `dot` binary on PATH.
"""

import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine
from sqlalchemy_schemadisplay import create_schema_graph

# Repo-root-relative output path (this file lives at backend/scripts/).
_OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "data-model.svg"


def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Set DATABASE_URL to a database migrated to head.")

    # Reflect the migrated schema, dropping Alembic's bookkeeping table.
    engine = create_engine(url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    tables = [t for name, t in metadata.tables.items() if name != "alembic_version"]

    graph = create_schema_graph(
        engine,
        tables=tables,
        show_datatypes=True,
        show_indexes=True,
        show_column_keys=True,
        rankdir="LR",
        concentrate=False,
    )
    graph.write_svg(str(_OUTPUT))
    print(f"Wrote {_OUTPUT}")


if __name__ == "__main__":
    main()
