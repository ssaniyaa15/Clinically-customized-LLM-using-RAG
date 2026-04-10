from __future__ import annotations

from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from patients.storage_service import StorageService


class FakeMinioClient:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.created_bucket = False

    def bucket_exists(self, bucket: str) -> bool:
        _ = bucket
        return self.created_bucket

    def make_bucket(self, bucket: str) -> None:
        _ = bucket
        self.created_bucket = True

    def put_object(self, bucket_name: str, object_name: str, data: BytesIO, length: int, content_type: str) -> None:
        _ = (bucket_name, length, content_type)
        self.objects[object_name] = data.read()

    def presigned_get_object(self, bucket_name: str, object_name: str, expires) -> str:  # type: ignore[no-untyped-def]
        _ = expires
        return f"https://fake.local/{bucket_name}/{object_name}"

    def remove_object(self, bucket_name: str, object_name: str) -> None:
        _ = bucket_name
        if object_name in self.objects:
            del self.objects[object_name]


@pytest.mark.asyncio
async def test_storage_upload_and_presign_and_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeMinioClient()
    monkeypatch.setattr(StorageService, "_build_client", lambda self: fake)
    service = StorageService(
        endpoint="localhost:9000", access_key="k", secret_key="s", bucket="clinical-records"
    )
    upload = UploadFile(
        filename="report.pdf",
        file=BytesIO(b"hello"),
        headers=Headers({"content-type": "application/pdf"}),
    )
    key = await service.upload_file(uuid4(), upload, "lab_report")
    assert key.startswith("patients/")
    url = service.get_presigned_url(key, expires_hours=1)
    assert "https://fake.local/clinical-records/" in url
    assert service.delete_file(key)

