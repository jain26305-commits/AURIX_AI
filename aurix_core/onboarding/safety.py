"""Defensive file inspection, path sanitization, and payload safety validator for Phase 11."""

import os
import re
from typing import Any, Dict, List, Optional, Tuple
from aurix_core.config.settings import settings
from aurix_core.onboarding.contracts import SourceType

# Magic byte signatures
ZIP_MAGIC_BYTES = b"PK\x03\x04"


class FileSafetyException(Exception):
    """Exception raised when an uploaded file or payload violates security constraints."""

    def __init__(self, message: str, code: str = "FILE_SAFETY_VIOLATION", reason: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.reason = reason or code


class FileSafetyValidator:
    """Defensive file inspection, content validation, and filename sanitizer."""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitizes raw filenames by removing path traversal characters, directory paths,
        and null bytes.
        """
        if not filename or not filename.strip():
            return "unnamed_upload.dat"

        # Remove null bytes
        cleaned = filename.replace("\x00", "")

        # Normalize slashes
        cleaned = cleaned.replace("\\", "/")

        # Strip leading relative path traversal sequences
        while cleaned.startswith("../") or cleaned.startswith("./"):
            if cleaned.startswith("../"):
                cleaned = cleaned[3:]
            elif cleaned.startswith("./"):
                cleaned = cleaned[2:]

        # Replace directory separators with underscores to preserve descriptive names
        cleaned = cleaned.replace("/", "_")

        # Strip multiple dots
        cleaned = re.sub(r"\.\.+", ".", cleaned)

        # Retain only safe alphanumeric characters, dashes, underscores, and dots
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned)
        cleaned = cleaned.strip("._")

        return cleaned if cleaned else "sanitized_upload.dat"

    @classmethod
    def detect_source_type(cls, filename: str) -> SourceType:
        """Detects file format source type based on extension."""
        lower_name = filename.lower()
        if lower_name.endswith(".csv"):
            return SourceType.CSV
        elif lower_name.endswith((".xlsx", ".xls")):
            return SourceType.XLSX
        elif lower_name.endswith(".json"):
            return SourceType.JSON
        else:
            raise FileSafetyException(
                f"Unsupported file extension in '{filename}'. "
                f"Allowed extensions: {settings.allowed_upload_extensions}",
                code="INVALID_EXTENSION",
            )

    @classmethod
    def validate_file(
        cls,
        filename: str,
        content: bytes,
        max_size_bytes: Optional[int] = None,
    ) -> Tuple[str, SourceType]:
        """
        Validates file size, extension whitelisting, and magic bytes.
        Returns: (sanitized_filename: str, source_type: SourceType)
        """
        limit = max_size_bytes or settings.max_upload_file_size_bytes

        # 1. Size Validation
        if len(content) == 0:
            raise FileSafetyException("Uploaded file is empty (0 bytes).", code="EMPTY_FILE")

        if len(content) > limit:
            raise FileSafetyException(
                f"File size ({len(content)} bytes) exceeds the maximum allowed limit of {limit} bytes.",
                code="FILE_TOO_LARGE",
            )

        # 2. Filename & Extension Sanitization
        clean_name = cls.sanitize_filename(filename)
        ext = os.path.splitext(clean_name)[1].lower()

        if ext not in settings.allowed_upload_extensions:
            allowed = ", ".join(settings.allowed_upload_extensions)
            raise FileSafetyException(
                f"Unsupported file extension '{ext}'. Allowed extensions: [{allowed}].",
                code="INVALID_EXTENSION",
            )

        # 3. Magic Byte & Content Structure Inspection
        source_type: SourceType
        if ext in [".xlsx", ".xls"]:
            source_type = SourceType.XLSX
            if not content.startswith(ZIP_MAGIC_BYTES) and ext == ".xlsx":
                raise FileSafetyException(
                    "Invalid XLSX spreadsheet. File content does not match standard OpenXML ZIP archive structure.",
                    code="CORRUPTED_SPREADSHEET",
                )
        elif ext == ".json":
            source_type = SourceType.JSON
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                raise FileSafetyException(
                    "Malformed JSON file. Content is not valid UTF-8 text.",
                    code="INVALID_ENCODING",
                )
        elif ext == ".csv":
            source_type = SourceType.CSV
            try:
                content.decode("utf-8-sig")
            except UnicodeDecodeError:
                try:
                    content.decode("latin-1")
                except Exception:
                    raise FileSafetyException(
                        "Malformed CSV file. Content encoding cannot be resolved.",
                        code="INVALID_ENCODING",
                    )
        else:
            source_type = SourceType.API

        return clean_name, source_type

    @classmethod
    def validate_raw_records(
        cls,
        records: Any,
        max_records: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Validates in-memory record collections (lists of dictionaries) from API or JSON payloads.
        """
        if not isinstance(records, list):
            raise FileSafetyException(
                "Payload records must be formatted as a JSON array of objects.",
                code="INVALID_RECORD_STRUCTURE",
            )

        if len(records) == 0:
            raise FileSafetyException(
                "Record collection is empty.",
                code="EMPTY_RECORDS",
            )

        limit = max_records or settings.max_onboarding_records_sync * 10
        if len(records) > limit:
            raise FileSafetyException(
                f"Record count ({len(records)}) exceeds maximum single ingestion limit of {limit}.",
                code="RECORD_COUNT_EXCEEDED",
            )

        for i, row in enumerate(records[:100]):  # Sample check first 100
            if not isinstance(row, dict):
                raise FileSafetyException(
                    f"Record at index {i} is not a valid dictionary object.",
                    code="MALFORMED_RECORD_ITEM",
                )

        return records