from pathlib import Path

from preprocessing.harmonisation import HarmonisationService


def test_map_code_returns_canonical(tmp_path: Path) -> None:
    csv_file = tmp_path / "ontology_mappings.csv"
    csv_file.write_text(
        "system,code,canonical_id,canonical_label\nICD10,I10,CAN-HTN,Hypertension\n",
        encoding="utf-8",
    )
    db_file = tmp_path / "ontology.db"
    svc = HarmonisationService(db_url=f"sqlite:///{db_file}", csv_path=str(csv_file))

    result = svc.map_code("ICD10", "I10")
    assert result is not None
    assert result.canonical_id == "CAN-HTN"


def test_map_code_returns_none_for_missing(tmp_path: Path) -> None:
    csv_file = tmp_path / "ontology_mappings.csv"
    csv_file.write_text(
        "system,code,canonical_id,canonical_label\nICD10,E11,CAN-T2D,Diabetes Type 2\n",
        encoding="utf-8",
    )
    db_file = tmp_path / "ontology.db"
    svc = HarmonisationService(db_url=f"sqlite:///{db_file}", csv_path=str(csv_file))
    assert svc.map_code("LOINC", "1234-5") is None

