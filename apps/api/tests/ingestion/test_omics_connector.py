from pathlib import Path

from ingestion.omics_connector import OmicsConnector


def test_ingest_vcf(tmp_path: Path) -> None:
    path = tmp_path / "sample.vcf"
    path.write_text(
        "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\n1\t100\trs1\tA\tG\n1\t200\trs2\tC\tT\n",
        encoding="utf-8",
    )
    payload = OmicsConnector().ingest_file(str(path), sample_id="SNP-1")
    assert payload.omics_type == "snp"
    assert payload.sample_id == "SNP-1"
    assert payload.feature_count == 2


def test_ingest_rnaseq_csv(tmp_path: Path) -> None:
    path = tmp_path / "rna_counts.csv"
    path.write_text("gene,count\nTP53,10\nBRCA1,12\n", encoding="utf-8")
    payload = OmicsConnector().ingest_file(str(path))
    assert payload.omics_type == "rna_seq"
    assert payload.feature_count == 2

