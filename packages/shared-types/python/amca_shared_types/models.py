from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check payload shared with the web client."""

    status: str = Field(..., description="Overall health status")
    service: str = Field(..., description="Logical service name")
