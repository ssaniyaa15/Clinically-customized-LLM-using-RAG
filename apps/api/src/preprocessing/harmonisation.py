from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Column, MetaData, String, Table, create_engine, select
from sqlalchemy.engine import Engine


@dataclass
class CanonicalCode:
    system: str
    code: str
    canonical_id: str
    canonical_label: str


class HarmonisationService:
    def __init__(
        self,
        db_url: str = "sqlite:///apps/api/data/ontology_mappings.db",
        csv_path: str = "apps/api/data/ontology_mappings.csv",
    ) -> None:
        self.engine: Engine = create_engine(db_url, future=True)
        self.metadata = MetaData()
        self.mappings = Table(
            "ontology_mappings",
            self.metadata,
            Column("system", String, nullable=False),
            Column("code", String, nullable=False),
            Column("canonical_id", String, nullable=False),
            Column("canonical_label", String, nullable=False),
        )
        self.metadata.create_all(self.engine)
        self._bootstrap_from_csv(Path(csv_path))

    def _bootstrap_from_csv(self, csv_path: Path) -> None:
        if not csv_path.exists():
            return
        with self.engine.begin() as conn, csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = [
                {
                    "system": (row.get("system") or "").strip().upper(),
                    "code": (row.get("code") or "").strip(),
                    "canonical_id": (row.get("canonical_id") or "").strip(),
                    "canonical_label": (row.get("canonical_label") or "").strip(),
                }
                for row in reader
                if row.get("system") and row.get("code")
            ]
            if rows:
                conn.execute(self.mappings.delete())
                conn.execute(self.mappings.insert(), rows)

    def map_code(self, system: str, code: str) -> CanonicalCode | None:
        stmt = select(self.mappings).where(
            self.mappings.c.system == system.upper(), self.mappings.c.code == code
        )
        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return CanonicalCode(
            system=row["system"],
            code=row["code"],
            canonical_id=row["canonical_id"],
            canonical_label=row["canonical_label"],
        )

