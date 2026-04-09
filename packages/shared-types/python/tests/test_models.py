from amca_shared_types.models import HealthResponse


def test_health_response() -> None:
    m = HealthResponse(status="ok", service="test")
    assert m.model_dump() == {"status": "ok", "service": "test"}
