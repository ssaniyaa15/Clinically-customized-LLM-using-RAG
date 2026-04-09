from __future__ import annotations

import csv
from pathlib import Path

from pydantic import BaseModel


class OmicsPayload(BaseModel):
    omics_type: str
    sample_id: str
    feature_count: int
    raw_data_path: str


class OmicsConnector:
    def ingest_file(self, file_path: str, sample_id: str | None = None) -> OmicsPayload:
        path = Path(file_path)
        omics_type = self._infer_omics_type(path)
        count = self._count_features(path, omics_type)
        sid = sample_id or path.stem
        return OmicsPayload(
            omics_type=omics_type,
            sample_id=sid,
            feature_count=count,
            raw_data_path=str(path),
        )

    @staticmethod
    def _infer_omics_type(path: Path) -> str:
        name = path.name.lower()
        if path.suffix.lower() == ".vcf":
            return "snp"
        if "proteom" in name:
            return "proteomics"
        return "rna_seq"

    @staticmethod
    def _count_features(path: Path, omics_type: str) -> int:
        if omics_type == "snp":
            with path.open("r", encoding="utf-8") as handle:
                return sum(1 for line in handle if line.strip() and not line.startswith("#"))

        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
            if not rows:
                return 0
            return max(0, len(rows) - 1)

