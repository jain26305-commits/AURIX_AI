"""Global application configuration management for AURIX Enterprise Platform.

Configuration is environment-driven and validated at startup. Production
settings fail fast when security-critical values are unsafe.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings loaded from environment variables or .env."""

    app_name: str = "AURIX Enterprise Supply Chain Platform"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./aurix_enterprise.db"
    alembic_database_url: str = Field(
        default="",
        description="Explicit database URL override for Alembic migration execution.",
    )
    database_disable_prepared_statements: bool = Field(default=False)

    # Multi-tenancy
    default_tenant_id: str = "default_tenant"

    database_pool_size: int = Field(default=5)
    database_max_overflow: int = Field(default=10)
    database_pool_timeout_seconds: int = Field(default=30)
    database_pool_recycle_seconds: int = Field(default=1800)
    database_connect_timeout_seconds: int = Field(default=10)
    database_statement_timeout_ms: int = Field(default=30000)

    # Artifact storage
    artifact_storage_path: str = "./artifacts"
    artifact_storage_backend: Literal["local", "supabase"] = "local"
    artifact_storage_bucket: str = "aurix-artifacts"
    artifact_storage_prefix: str = "models"
    artifact_storage_timeout_seconds: int = 30
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Runtime build identity
    build_version: str = Field(default="16.0.0")
    schema_version: str = Field(default="1.0.0")
    release_commit: str = Field(default="HEAD")

    # Data retention
    retention_days_runs: int = Field(default=90)
    retention_days_events: int = Field(default=30)
    retention_days_quarantine: int = Field(default=60)
    retention_days_artifacts: int = Field(default=180)
    retention_days_action_audits: int = Field(default=365)

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")
    enable_docs: bool = Field(default=True)

    # Security / authentication
    # Intentionally not a real secret. Production validation below rejects it.
    api_secret_key: str = Field(
        default="",
        description="Secret key for signing authentication tokens; required in production.",
    )
    api_algorithm: str = Field(default="HS256")
    api_access_token_expire_minutes: int = Field(default=1440)
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
        ]
    )

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=120)
    rate_limit_ai_requests_per_minute: int = Field(default=30)

    # AI quota
    ai_monthly_spend_limit_usd: float = Field(default=500.0)
    ai_daily_spend_limit_usd: float = Field(default=50.0)
    ai_monthly_token_limit: int = Field(default=10_000_000)
    ai_daily_token_limit: int = Field(default=1_000_000)
    ai_monthly_request_limit: int = Field(default=5000)
    ai_daily_request_limit: int = Field(default=500)
    ai_quota_warning_pct: float = Field(default=80.0)

    # Cloud AI providers
    gemini_api_key: str = Field(default="")
    cloudflare_account_id: str = Field(default="")
    cloudflare_api_token: str = Field(default="")

    # Automated onboarding
    max_upload_file_size_bytes: int = Field(default=26_214_400)
    allowed_upload_extensions: List[str] = Field(
        default_factory=lambda: [".csv", ".xlsx", ".xls", ".json"]
    )
    max_onboarding_records_sync: int = Field(default=5000)

    # Connectors
    connector_default_timeout_seconds: int = Field(default=60)
    connector_max_retry_attempts: int = Field(default=3)
    connector_retry_backoff_factor: float = Field(default=1.5)
    webhook_timestamp_tolerance_seconds: int = Field(default=300)
    reconciliation_material_variance_pct: float = Field(default=5.0)

    # Real-time events
    event_max_retry_attempts: int = Field(default=3)
    event_retry_backoff_factor: float = Field(default=1.5)
    event_deduplication_window_seconds: int = Field(default=86400)

    # Controlled execution
    action_approval_financial_threshold: float = Field(default=50000.0)
    action_max_retry_attempts: int = Field(default=3)
    action_default_expiry_hours: int = Field(default=24)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        value = str(value).strip().lower()
        allowed = {"development", "test", "staging", "production"}
        if value not in allowed:
            raise ValueError(
                f"environment must be one of: {', '.join(sorted(allowed))}"
            )
        return value

    @field_validator("database_url", "default_tenant_id", mode="before")
    @classmethod
    def require_non_empty_string(cls, value: str) -> str:
        value = str(value).strip()
        if not value:
            raise ValueError("configuration value cannot be empty")
        return value

    @field_validator("api_prefix", mode="before")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        value = str(value).strip()
        if not value:
            raise ValueError("api_prefix cannot be empty")
        return "/" + value.strip("/")

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        """Validate security-critical and operational configuration invariants."""

        if self.api_port < 1 or self.api_port > 65535:
            raise ValueError("api_port must be between 1 and 65535")

        positive_ints = {
            "api_access_token_expire_minutes": self.api_access_token_expire_minutes,
            "database_pool_size": self.database_pool_size,
            "database_max_overflow": self.database_max_overflow,
            "database_pool_timeout_seconds": self.database_pool_timeout_seconds,
            "database_pool_recycle_seconds": self.database_pool_recycle_seconds,
            "database_connect_timeout_seconds": self.database_connect_timeout_seconds,
            "database_statement_timeout_ms": self.database_statement_timeout_ms,
            "rate_limit_requests_per_minute": self.rate_limit_requests_per_minute,
            "rate_limit_ai_requests_per_minute": self.rate_limit_ai_requests_per_minute,
            "ai_monthly_token_limit": self.ai_monthly_token_limit,
            "ai_daily_token_limit": self.ai_daily_token_limit,
            "ai_monthly_request_limit": self.ai_monthly_request_limit,
            "ai_daily_request_limit": self.ai_daily_request_limit,
            "max_upload_file_size_bytes": self.max_upload_file_size_bytes,
            "max_onboarding_records_sync": self.max_onboarding_records_sync,
            "artifact_storage_timeout_seconds": self.artifact_storage_timeout_seconds,
            "connector_default_timeout_seconds": self.connector_default_timeout_seconds,
            "connector_max_retry_attempts": self.connector_max_retry_attempts,
            "webhook_timestamp_tolerance_seconds": self.webhook_timestamp_tolerance_seconds,
            "event_max_retry_attempts": self.event_max_retry_attempts,
            "event_deduplication_window_seconds": self.event_deduplication_window_seconds,
            "action_max_retry_attempts": self.action_max_retry_attempts,
            "action_default_expiry_hours": self.action_default_expiry_hours,
            "retention_days_runs": self.retention_days_runs,
            "retention_days_events": self.retention_days_events,
            "retention_days_quarantine": self.retention_days_quarantine,
            "retention_days_artifacts": self.retention_days_artifacts,
            "retention_days_action_audits": self.retention_days_action_audits,
        }

        invalid = [name for name, value in positive_ints.items() if value <= 0]
        if invalid:
            raise ValueError(
                "These configuration values must be greater than zero: "
                + ", ".join(invalid)
            )

        if not 0.0 <= self.ai_quota_warning_pct <= 100.0:
            raise ValueError("ai_quota_warning_pct must be between 0 and 100")

        non_negative_floats = {
            "ai_monthly_spend_limit_usd": self.ai_monthly_spend_limit_usd,
            "ai_daily_spend_limit_usd": self.ai_daily_spend_limit_usd,
            "connector_retry_backoff_factor": self.connector_retry_backoff_factor,
            "event_retry_backoff_factor": self.event_retry_backoff_factor,
            "action_approval_financial_threshold": self.action_approval_financial_threshold,
            "reconciliation_material_variance_pct": self.reconciliation_material_variance_pct,
        }

        invalid_floats = [
            name for name, value in non_negative_floats.items()
            if value < 0
        ]
        if invalid_floats:
            raise ValueError(
                "These configuration values cannot be negative: "
                + ", ".join(invalid_floats)
            )

        if self.ai_daily_spend_limit_usd > self.ai_monthly_spend_limit_usd:
            raise ValueError(
                "ai_daily_spend_limit_usd cannot exceed ai_monthly_spend_limit_usd"
            )

        if self.ai_daily_token_limit > self.ai_monthly_token_limit:
            raise ValueError(
                "ai_daily_token_limit cannot exceed ai_monthly_token_limit"
            )

        if self.ai_daily_request_limit > self.ai_monthly_request_limit:
            raise ValueError(
                "ai_daily_request_limit cannot exceed ai_monthly_request_limit"
            )

        environment = self.environment

        if environment == "production":
            # Preserve the existing fail-fast contract: an explicitly enabled
            # debug mode is rejected before other production secret checks.
            if self.debug:
                raise ValueError(
                    "FATAL SECURITY VIOLATION: 'debug' mode must be disabled (False) in production."
                )

            # Production must not rely on the development secret or an empty one.
            secret = self.api_secret_key.strip()
            if not secret or len(secret) < 32:
                raise ValueError(
                    "FATAL SECURITY VIOLATION: 'api_secret_key' must be at least 32 characters long in production."
                )

            if secret.lower().startswith("aurix-dev-secret-key"):
                raise ValueError(
                    "FATAL SECURITY VIOLATION: production cannot use a development api_secret_key."
                )

            if self.database_url.startswith("sqlite://"):
                raise ValueError(
                    "FATAL SECURITY VIOLATION: SQLite is not permitted for production."
                )

            if self.artifact_storage_backend != "supabase":
                raise ValueError(
                    "FATAL CONFIGURATION VIOLATION: production artifact storage "
                    "must use the durable Supabase backend."
                )

            if not self.supabase_url.strip() or not self.supabase_service_role_key.strip():
                raise ValueError(
                    "FATAL CONFIGURATION VIOLATION: production artifact storage "
                    "requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
                )

            if not self.artifact_storage_bucket.strip():
                raise ValueError(
                    "FATAL CONFIGURATION VIOLATION: artifact storage bucket cannot be empty."
                )

            if self.enable_docs:
                raise ValueError(
                    "FATAL SECURITY VIOLATION: API documentation endpoints "
                    "must be disabled in production."
                )

            if any(origin.strip() == "*" for origin in self.cors_origins):
                raise ValueError(
                    "FATAL SECURITY VIOLATION: wildcard CORS is not permitted in production."
                )

        return self


settings = Settings()