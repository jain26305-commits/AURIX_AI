# AURIX PHASE 2: PERSISTENT DATA INGESTION & LIFECYCLE FOUNDATION

## Objective
Establish a secure, idempotent, and tenant-isolated Data Ingestion capability that converts external operational data (CSVs, ERP feeds) into Canonical SQLAlchemy records.

## Architecture
The ingestion architecture enforces a strict boundary to protect the analytical engines:
`Source` → `IngestionService (Hashing)` → `DataQualityEngine (Validation)` → `CanonicalMapper (Upserts)` → `Database`

## Files Created & Modified
**Created:**
- `aurix_core/database/models/ingestion.py` (IngestionRun tracking)
- `aurix_core/data_foundation/quality_engine.py` (Validation constraints)
- `aurix_core/data_foundation/ingestion_service.py` (Orchestration & Idempotency)
- `tests/test_phase2_ingestion.py`
- `docs/AURIX_PHASE_2_IMPLEMENTATION.md`

**Modified:**
- `aurix_core/database/models/supply_chain.py` (Added `ingestion_run_id` for provenance)
- `aurix_core/database/init_db.py` (Registered ingestion models)
- `aurix_core/data_foundation/db_mapper.py` (Enabled Upserts & Provenance tagging)
- `docs/AURIX_IMPLEMENTATION_LEDGER.md`

**Deliberately Untouched:**
- All Phase 2-9 analytical engines. They await clean, database-sourced execution integration in a future phase.

## Validation & Isolation Rules
- **Validation:** Strict rejection of negative physical inventory quantities and missing identifiers via `DataQualityEngine`. Zero fabrication is enforced.
- **Idempotency:** Datasets are hashed via SHA-256 (`pd.DataFrame.to_json`). Identical uploads are instantly flagged as `DUPLICATE` to prevent database churn.
- **Tenant Isolation:** Enforced implicitly by injecting `tenant_id` at the `BaseRepository` and `IngestionRun` levels.

## Known Limitations & Future Points
- Dataframes are currently hashed entirely in-memory. For files >2GB, chunked hash reading will be required.
- No asynchronous queueing (e.g., Celery) is implemented yet, limiting parallel multi-tenant bulk uploads.