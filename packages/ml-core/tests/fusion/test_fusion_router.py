import numpy as np
import pandas as pd
import torch
from _pytest.monkeypatch import MonkeyPatch

from fusion.cross_modal_attention import CrossModalEmbedding
from fusion.fusion_router import FusionRouter
from preprocessing.deidentification import DeidentifiedRecord
from preprocessing.harmonisation import CanonicalCode
from preprocessing.image_preprocessing import ProcessedImagePayload, SegmentationMask
from preprocessing.imputation_qc import ImputedDataFrame
from preprocessing.preprocessor_pipeline import PipelineRunLog, PreprocessedBundle


def _make_bundle() -> PreprocessedBundle:
    return PreprocessedBundle(
        harmonised_codes=[CanonicalCode("ICD10", "I10", "C1", "Hypertension")],
        deidentified_record=DeidentifiedRecord(
            patient_id="P1",
            deidentified_text="clinical summary",
            structured_record={},
        ),
        imputed_data=ImputedDataFrame(
            imputed_df=pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]}),
            outlier_flags=[],
            imputation_report={},
        ),
        processed_image=ProcessedImagePayload(
            normalised_tensor=np.ones((224, 224), dtype=np.float32),
            augmentation_applied=[],
            mask=SegmentationMask(),
        ),
        pipeline_log=PipelineRunLog(run_id="r1"),
    )


def test_extract_inputs_shapes() -> None:
    bundle = _make_bundle()
    ehr, omics, texts, image = FusionRouter._extract_inputs(bundle)
    assert ehr.tensor.shape == (1, 256)
    assert omics.tensor.shape == (1, 256)
    assert len(texts) == 1
    assert image.shape[1] == 3


def test_fusion_router_forward(monkeypatch: MonkeyPatch) -> None:
    router = FusionRouter(num_classes=3)
    bundle = _make_bundle()

    monkeypatch.setattr(
        router.cross_modal,
        "forward",
        lambda texts, images: CrossModalEmbedding(tensor=torch.randn(1, 768)),
    )

    out = router(bundle)
    assert out.early_embedding.tensor.shape == (1, 512)
    assert out.cross_modal_embedding.tensor.shape == (1, 768)
    assert out.late_output.final_logits.shape == (1, 3)
    assert "tabular" in out.available_modalities

