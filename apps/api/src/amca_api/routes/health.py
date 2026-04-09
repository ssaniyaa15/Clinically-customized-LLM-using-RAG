from fastapi import APIRouter

from amca_shared_types.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="amca-api")
