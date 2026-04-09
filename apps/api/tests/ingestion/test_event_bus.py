import json
from datetime import datetime
from typing import Any

from _pytest.monkeypatch import MonkeyPatch

from ingestion.event_bus import EventBus


class FakeProducer:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.topic: str | None = None
        self.value: bytes | None = None

    def produce(self, topic: str, value: bytes) -> None:
        self.topic = topic
        self.value = value

    def poll(self, _timeout: int) -> None:
        return None


def test_publish_event(monkeypatch: MonkeyPatch) -> None:
    fake_producer = FakeProducer()
    monkeypatch.setattr("ingestion.event_bus.Producer", lambda _cfg: fake_producer)

    bus = EventBus({"bootstrap.servers": "kafka:9092"}, schema_version="2.0.0")
    envelope = bus.publish_event(
        topic="clinical.events",
        payload={"modality": "wearable", "signal": "spo2"},
        patient_id="P100",
        timestamp=datetime(2026, 4, 9, 12, 0, 0),
    )

    assert envelope["patient_id"] == "P100"
    assert envelope["modality"] == "wearable"
    assert envelope["schema_version"] == "2.0.0"
    assert fake_producer.topic == "clinical.events"
    value = fake_producer.value
    assert value is not None
    sent = json.loads(value.decode("utf-8"))
    assert sent["payload"]["signal"] == "spo2"

