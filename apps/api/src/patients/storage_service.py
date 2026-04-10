from __future__ import annotations

import os
from datetime import timedelta
from io import BytesIO
from typing import Any
from uuid import UUID, uuid4

from fastapi import UploadFile

minio_module: Any = None
try:
    import minio as minio_module
except Exception:  # pragma: no cover
    minio_module = None


class StorageService:
    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        secure: bool | None = None,
    ) -> None:
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT") or "localhost:9000"
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY") or "minioadmin"
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY") or "minioadmin"
        self.bucket = bucket or os.getenv("MINIO_BUCKET") or "clinical-records"
        if secure is None:
            secure = self.endpoint.startswith("https://")
        self.secure = secure
        self.client: Any = self._build_client()

    def _build_client(self) -> Any:
        if minio_module is None:
            return None
        Minio = getattr(minio_module, "Minio", None)
        if Minio is None:
            return None
        endpoint = self.endpoint.replace("http://", "").replace("https://", "")
        client = Minio(
            endpoint=endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
        if not client.bucket_exists(self.bucket):
            client.make_bucket(self.bucket)
        return client

    @staticmethod
    def _safe_filename(filename: str | None) -> str:
        if not filename:
            return "upload.bin"
        return filename.replace("\\", "_").replace("/", "_")

    def build_object_key(self, patient_id: UUID, record_type: str, filename: str) -> str:
        return f"patients/{patient_id}/{record_type}/{uuid4()}_{self._safe_filename(filename)}"

    async def upload_file(self, patient_id: UUID, file: UploadFile, record_type: str) -> str:
        object_key = self.build_object_key(patient_id, record_type, file.filename or "upload.bin")
        payload = await file.read()
        if self.client is None:
            return object_key
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_key,
            data=BytesIO(payload),
            length=len(payload),
            content_type=file.content_type or "application/octet-stream",
        )
        return object_key

    def get_presigned_url(self, object_key: str, expires_hours: int = 24) -> str:
        if self.client is None:
            return f"http://{self.endpoint}/{self.bucket}/{object_key}"
        return str(
            self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=object_key,
                expires=timedelta(hours=expires_hours),
            )
        )

    def delete_file(self, object_key: str) -> bool:
        if self.client is None:
            return True
        try:
            self.client.remove_object(self.bucket, object_key)
            return True
        except Exception:
            return False

