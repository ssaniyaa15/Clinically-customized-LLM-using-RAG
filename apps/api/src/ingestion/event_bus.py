from __future__ import annotations

import json
from datetime import datetime
from typing import Any, cast

confluent_kafka: Any
try:
    import confluent_kafka
except ImportError:  # pragma: no cover
    confluent_kafka = None

Producer: Any = getattr(confluent_kafka, "Producer", None)


class EventBus:
    def __init__(self, producer_config: dict[str, Any], schema_version: str = "1.0.0") -> None:
        if Producer is None:
            raise RuntimeError("confluent-kafka dependency not installed.")
        self.producer = cast(Any, Producer)(producer_config)
        self.schema_version = schema_version

    def publish_event(
        self,
        topic: str,
        payload: dict[str, Any],
        patient_id: str,
        timestamp: datetime,
    ) -> dict[str, Any]:
        envelope = {
            "patient_id": patient_id,
            "modality": payload.get("modality", "unknown"),
            "timestamp": timestamp.isoformat(),
            "schema_version": self.schema_version,
            "payload": payload,
        }
        self.producer.produce(topic, value=json.dumps(envelope).encode("utf-8"))
        self.producer.poll(0)
        return envelope

