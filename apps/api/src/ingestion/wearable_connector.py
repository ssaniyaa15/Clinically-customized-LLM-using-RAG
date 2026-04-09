from __future__ import annotations

import json
from datetime import datetime
from typing import Any, cast

from pydantic import BaseModel, Field

confluent_kafka: Any
try:
    import confluent_kafka
except ImportError:  # pragma: no cover
    confluent_kafka = None

Consumer: Any = getattr(confluent_kafka, "Consumer", None)


class VitalsStream(BaseModel):
    patient_id: str
    timestamp: datetime
    ecg: dict[str, Any] | None = None
    spo2: dict[str, Any] | None = None
    actigraphy: dict[str, Any] | None = None
    source_topic: str = Field(default="wearable.vitals")


class WearableConnector:
    topic = "wearable.vitals"

    def __init__(self, consumer_config: dict[str, Any]) -> None:
        if Consumer is None:
            raise RuntimeError("confluent-kafka dependency not installed.")
        self.consumer = cast(Any, Consumer)(consumer_config)
        self.consumer.subscribe([self.topic])

    @staticmethod
    def parse_payload(payload: str | dict[str, Any]) -> VitalsStream:
        data = json.loads(payload) if isinstance(payload, str) else payload
        return VitalsStream(
            patient_id=str(data["patient_id"]),
            timestamp=datetime.fromisoformat(str(data["timestamp"])),
            ecg=data.get("ecg"),
            spo2=data.get("spo2"),
            actigraphy=data.get("actigraphy"),
        )

    def consume_once(self, timeout: float = 1.0) -> VitalsStream | None:
        msg = self.consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            raise RuntimeError(str(msg.error()))
        raw = msg.value()
        payload = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
        return self.parse_payload(payload)

