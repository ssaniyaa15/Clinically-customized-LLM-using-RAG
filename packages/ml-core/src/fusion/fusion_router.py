from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn

from preprocessing.preprocessor_pipeline import PreprocessedBundle

from fusion.cross_modal_attention import CrossModalAttentionFusion, CrossModalEmbedding
from fusion.early_fusion import EHREmbedding, EarlyFusionMLP, JointEmbedding, OmicsEmbedding
from fusion.late_fusion import LateFusionEnsembler, LateFusionOutput, ModalityOutput


@dataclass
class FusedRepresentation:
    early_embedding: JointEmbedding
    cross_modal_embedding: CrossModalEmbedding
    late_output: LateFusionOutput
    available_modalities: list[str]


class FusionRouter(nn.Module):
    """Routes a preprocessed bundle through early, cross-modal, and late fusion heads."""

    def __init__(self, num_classes: int = 4) -> None:
        super().__init__()
        self.early_fusion = EarlyFusionMLP()
        self.cross_modal = CrossModalAttentionFusion()
        self.late_fusion = LateFusionEnsembler(num_classes=num_classes)
        self.early_head = nn.Linear(512, num_classes)
        self.cross_head = nn.Linear(768, num_classes)
        self.tabular_head = nn.Linear(512, num_classes)

    def forward(self, bundle: PreprocessedBundle) -> FusedRepresentation:
        ehr_embedding, omics_embedding, texts, images = self._extract_inputs(bundle)
        early = self.early_fusion(ehr_embedding=ehr_embedding, omics_embedding=omics_embedding)
        cross = self.cross_modal(texts=texts, images=images)

        early_logits = self.early_head(early.tensor)
        cross_logits = self.cross_head(cross.tensor)
        tabular_logits = self.tabular_head(torch.cat([ehr_embedding.tensor, omics_embedding.tensor], dim=-1))

        # Bundle is used to detect currently available modalities.
        modalities = []
        if getattr(bundle, "deidentified_record", None) is not None:
            modalities.append("tabular")
        if getattr(bundle, "processed_image", None) is not None:
            modalities.append("imaging")
        if texts:
            modalities.append("clinical_text")

        late = self.late_fusion(
            ModalityOutput(name="early", logits=early_logits, modality_present="tabular" in modalities),
            ModalityOutput(name="cross", logits=cross_logits, modality_present="imaging" in modalities),
            ModalityOutput(name="tabular", logits=tabular_logits, modality_present="clinical_text" in modalities),
        )
        return FusedRepresentation(
            early_embedding=early,
            cross_modal_embedding=cross,
            late_output=late,
            available_modalities=modalities,
        )

    @staticmethod
    def _extract_inputs(
        bundle: PreprocessedBundle,
    ) -> tuple[EHREmbedding, OmicsEmbedding, list[str], Tensor]:
        imputed = bundle.imputed_data.imputed_df
        numeric = imputed.select_dtypes(include=["number"])
        if numeric.empty:
            base = torch.zeros((1, 256), dtype=torch.float32)
        else:
            vec = torch.tensor(numeric.mean(axis=0).to_numpy(), dtype=torch.float32).flatten()
            padded = torch.nn.functional.pad(vec, (0, max(0, 256 - vec.numel())))
            base = padded[:256].unsqueeze(0)

        ehr = EHREmbedding(tensor=base)
        omics = OmicsEmbedding(tensor=base.clone())

        text = bundle.deidentified_record.deidentified_text or ""
        texts = [text] if text else ["clinical note unavailable"]

        image_array = bundle.processed_image.normalised_tensor
        image = torch.tensor(image_array, dtype=torch.float32)
        if image.ndim == 2:
            image = image.unsqueeze(0).unsqueeze(0)
        elif image.ndim == 3:
            image = image.unsqueeze(0)
        image = image.repeat(1, max(1, 3 // image.shape[1]), 1, 1)
        image = image[:, :3, :, :]

        return ehr, omics, texts, image

