"""Durable model/artifact storage with local development and Supabase Storage backends."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from urllib.parse import quote

import requests

from aurix_core.config.settings import settings


class ArtifactStorage:
    """Stores model artifacts durably while preserving local-test compatibility."""

    @staticmethod
    def _safe_component(value: str) -> str:
        """Return a filesystem/object-key safe single path component."""
        cleaned = value.strip().replace("\\", "/").strip("/")
        if not cleaned or cleaned in {".", ".."} or ".." in cleaned.split("/"):
            raise ValueError("Unsafe artifact path component")
        return cleaned.replace("/", "_")

    @classmethod
    def build_key(
        cls,
        tenant_id: str,
        model_type: str,
        version: str,
        filename: str,
    ) -> str:
        """Build a tenant-scoped object-storage key."""
        parts = [
            settings.artifact_storage_prefix.strip("/"),
            cls._safe_component(tenant_id),
            cls._safe_component(model_type),
            cls._safe_component(version),
            cls._safe_component(filename),
        ]
        return "/".join(part for part in parts if part)

    @classmethod
    def _use_supabase(cls) -> bool:
        return settings.artifact_storage_backend == "supabase"

    @classmethod
    def _require_supabase_config(cls) -> tuple[str, str, str]:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError(
                "Supabase Storage is selected but SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY are not configured."
            )
        return (
            settings.supabase_url.rstrip("/"),
            settings.supabase_service_role_key,
            settings.artifact_storage_bucket,
        )

    @classmethod
    def save_bytes(
        cls,
        tenant_id: str,
        model_type: str,
        version: str,
        filename: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Persist bytes and return a durable storage reference."""
        key = cls.build_key(tenant_id, model_type, version, filename)

        if not cls._use_supabase():
            root = Path(settings.artifact_storage_path)
            target = root / key
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=target.parent,
                prefix=f".{target.name}.",
                delete=False,
            ) as tmp:
                tmp.write(data)
                temp_path = Path(tmp.name)
            os.replace(temp_path, target)
            return str(target)

        base_url, service_key, bucket = cls._require_supabase_config()
        url = f"{base_url}/storage/v1/object/{quote(bucket, safe='')}/{quote(key, safe='/')}"
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {service_key}",
                "apikey": service_key,
                "Content-Type": content_type,
                "x-upsert": "true",
            },
            data=data,
            timeout=settings.artifact_storage_timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase Storage upload failed ({response.status_code}): "
                f"{response.text[:500]}"
            )
        return f"supabase://{bucket}/{key}"

    @classmethod
    def save_file(
        cls,
        tenant_id: str,
        model_type: str,
        version: str,
        filename: str,
        file_path: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Persist a local file through the configured artifact backend."""
        with open(file_path, "rb") as handle:
            return cls.save_bytes(
                tenant_id=tenant_id,
                model_type=model_type,
                version=version,
                filename=filename,
                data=handle.read(),
                content_type=content_type,
            )

    @classmethod
    def load_bytes(cls, reference: str) -> bytes:
        """Load an artifact by local path or Supabase object reference."""
        if reference.startswith("supabase://"):
            remainder = reference[len("supabase://") :]
            bucket, key = remainder.split("/", 1)
            base_url, service_key, _ = cls._require_supabase_config()
            url = f"{base_url}/storage/v1/object/{quote(bucket, safe='')}/{quote(key, safe='/')}"
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {service_key}",
                    "apikey": service_key,
                },
                timeout=settings.artifact_storage_timeout_seconds,
            )
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Supabase Storage download failed ({response.status_code}): "
                    f"{response.text[:500]}"
                )
            return response.content

        with open(reference, "rb") as handle:
            return handle.read()

    @classmethod
    def sha256_bytes(cls, data: bytes) -> str:
        """Compute the SHA-256 digest used for artifact integrity checks."""
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def verify_reference_checksum(cls, reference: str, expected_checksum: str) -> bool:
        """Verify the stored artifact content against an expected SHA-256 checksum."""
        actual = cls.sha256_bytes(cls.load_bytes(reference))
        return actual == expected_checksum
