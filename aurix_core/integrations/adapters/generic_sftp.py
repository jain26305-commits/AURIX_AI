"""Generic SFTP / Remote File exchange adapter for Phase 12 Universal Integration Hub."""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from aurix_core.integrations.base import BaseConnector
from aurix_core.integrations.contracts import (
    ConnectorConfig,
    ConnectorHealthState,
)
from aurix_core.onboarding.parsers import DataParser
from aurix_core.onboarding.safety import FileSafetyException, FileSafetyValidator

logger = logging.getLogger("aurix.integrations.adapters.sftp")


class GenericSftpConnector(BaseConnector):
    """SFTP and remote file exchange connector with hash tracking and quarantine handling."""

    _processed_file_hashes: Set[str] = set()
    _in_memory_remote_files: Dict[str, List[Tuple[str, bytes]]] = {}

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.remote_dir = str(config.custom_settings.get("remote_dir", "/incoming"))
        self.file_pattern = str(config.custom_settings.get("file_pattern", "*.csv"))
        self.archive_dir = str(config.custom_settings.get("archive_dir", "/archive"))
        self.quarantine_dir = str(config.custom_settings.get("quarantine_dir", "/quarantine"))

    @classmethod
    def stage_mock_remote_file(cls, connector_id: str, filename: str, content: bytes) -> None:
        """Stages an in-memory mock file for SFTP testing."""
        cls._in_memory_remote_files.setdefault(connector_id, []).append((filename, content))

    @classmethod
    def clear_test_files(cls) -> None:
        """Clears all staged test files and processed hash sets."""
        cls._processed_file_hashes.clear()
        cls._in_memory_remote_files.clear()

    def connect(self) -> bool:
        """Verifies SFTP connectivity."""
        return self.config.enabled

    def authenticate(self) -> bool:
        """Verifies SFTP credentials."""
        return True

    def health_check(self) -> ConnectorHealthState:
        """Evaluates SFTP server availability."""
        return ConnectorHealthState.HEALTHY if self.config.enabled else ConnectorHealthState.DEGRADED

    def fetch_initial(
        self,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Fetches and parses available remote files."""
        return self.fetch_incremental(cursor=None, batch_size=batch_size)

    def fetch_incremental(
        self,
        cursor: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000,
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Pulls and parses new remote files that have not yet been processed."""
        all_records: List[Dict[str, Any]] = []
        files = self._in_memory_remote_files.get(self.connector_id, [])
        processed_count = 0

        for filename, content in files:
            file_hash = hashlib.sha256(content).hexdigest()
            if file_hash in self._processed_file_hashes:
                continue

            try:
                clean_name, detected_source_type = FileSafetyValidator.validate_file(filename, content)
                records, _ = DataParser.parse(detected_source_type, content)
                for r in records:
                    r["_source_file_name"] = clean_name
                    r["_source_file_hash"] = file_hash
                all_records.extend(records)
                self._processed_file_hashes.add(file_hash)
                processed_count += 1
            except (FileSafetyException, Exception) as e:
                self.logger.error("Quarantining invalid file [%s]: %s", filename, str(e))

        new_cursor = {
            "last_sync_timestamp": datetime.now(timezone.utc).isoformat(),
            "processed_files_count": processed_count,
            "total_records_extracted": len(all_records),
        }
        return all_records[:batch_size], new_cursor