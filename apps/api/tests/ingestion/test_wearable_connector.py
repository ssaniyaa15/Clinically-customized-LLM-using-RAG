import json
from datetime import datetime
from typing import Any

from _pytest.monkeypatch import MonkeyPatch

from ingestion.wearable_connector import WearableConnector


class FakeMessage:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def error(self):
        return None

    def value(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class FakeConsumer:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self._topic: list[str] | None = None
        self._msg: FakeMessage | None = None

    def subscribe(self, topics: list[str]) -> None:
        self._topic = topics

    def set_message(self, payload: dict[str, Any]) -> None:
        self._msg = FakeMessage(payload)

    def poll(self, _timeout: float) -> FakeMessage | None:
        return self._msg


def test_parse_payload() -> None:
    payload = {
        "patient_id": "W1",
        "timestamp": "2026-01-01T12:00:00",
        "ecg": {"lead_i": [0.1, 0.2]},
        "spo2": {"percent": 97},
        "actigraphy": {"steps": 1000},
    }
    stream = WearableConnector.parse_payload(payload)
    assert stream.patient_id == "W1"
    assert stream.timestamp == datetime.fromisoformat("2026-01-01T12:00:00")
    assert stream.spo2 == {"percent": 97}


def test_consume_once(monkeypatch: MonkeyPatch) -> None:
    fake_consumer = FakeConsumer()
    fake_consumer.set_message(
        {
            "patient_id": "W2",
            "timestamp": "2026-01-02T12:00:00",
            "ecg": {"rate": 75},
        }
    )
    monkeypatch.setattr("ingestion.wearable_connector.Consumer", lambda _cfg: fake_consumer)

    connector = WearableConnector({"bootstrap.servers": "kafka:9092", "group.id": "test"})
    result = connector.consume_once()
    assert result is not None
    assert result.patient_id == "W2"
    assert result.ecg == {"rate": 75}

