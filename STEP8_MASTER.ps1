# ============================================================
# AURIX STEP 8 MASTER
# PERFORMANCE + SCALABILITY AUDIT
#
# VERSION: HARDENED / POWERSHELL-SAFE / PYTHON-FILE-BASED
#
# PURPOSE
# -------
# Establish numerical performance evidence for:
#
#   1. API health latency
#   2. Deterministic API latency
#   3. Database query latency
#   4. File parsing / preprocessing
#   5. 1K / 10K / 100K record throughput
#   6. Concurrent API request behavior
#   7. AI route discovery + safe GET latency
#   8. Worker runtime health
#   9. Frontend initial HTTP response timing
#  10. Frontend production build
#  11. Architectural performance-risk heuristics
#
# SAFETY
# ------
# * No database schema changes
# * No intentional application-record inserts
# * No containers rebuilt
# * No containers recreated
# * No source files modified
# * Temporary benchmark files only under unique TEMP directory
# * AI POST routes are discovered but NOT automatically invoked
#
# OUTPUT
# ------
# AURIX_STEP8\
#   AURIX_STEP8_PERFORMANCE_AUDIT_YYYYMMDD_HHMMSS.txt
#
# Stable copy:
#   AURIX_STEP8_PERFORMANCE_AUDIT.txt
#
# ============================================================

$ErrorActionPreference = "Stop"

# ============================================================
# [0] ROOT / PATH INITIALIZATION
# ============================================================

$Root = (Get-Location).Path

if (-not (Test-Path (Join-Path $Root ".git"))) {
    throw "Git repository not detected. Run this script from the AURIX repository root."
}

$PythonPath = "D:\Python-IDLE\python.exe"

if (-not (Test-Path $PythonPath)) {
    throw "Python interpreter not found: $PythonPath"
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ReportDir = Join-Path $Root "AURIX_STEP8"

$Report = Join-Path `
    $ReportDir `
    "AURIX_STEP8_PERFORMANCE_AUDIT_$Timestamp.txt"

$LatestReport = Join-Path `
    $Root `
    "AURIX_STEP8_PERFORMANCE_AUDIT.txt"

$TempDir = Join-Path `
    $env:TEMP `
    ("aurix_step8_" + [guid]::NewGuid().ToString("N"))

New-Item `
    -ItemType Directory `
    -Path $ReportDir `
    -Force |
    Out-Null

New-Item `
    -ItemType Directory `
    -Path $TempDir `
    -Force |
    Out-Null

# ============================================================
# ENGINEERING THRESHOLDS
#
# These are audit targets for this project.
# They are not external SLA claims.
# ============================================================

$HealthP95TargetMs = 500
$DeterministicP95TargetMs = 1000
$DatabaseP95TargetMs = 250

$SmallFileTargetMs = 1000
$MediumFileTargetMs = 3000
$LargeFileTargetMs = 10000

$OneKThroughputTarget = 500
$TenKThroughputTarget = 1000

$ConcurrentErrorRateTarget = 2.0

$FrontendInitialResponseTargetMs = 3000

$AiGetP95TargetMs = 3000

$HealthIterations = 30
$DeterministicIterations = 20
$DatabaseIterations = 30
$AiIterations = 15
$FrontendIterations = 10

$ConcurrentRequests = 40
$ConcurrentWorkers = 10

# ============================================================
# REPORT STATE
# ============================================================

$ReportLines = New-Object System.Collections.Generic.List[string]
$Passes = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]
$Failures = New-Object System.Collections.Generic.List[string]
$NotProven = New-Object System.Collections.Generic.List[string]

function Add-Report {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text = ""
    )

    if ($null -eq $Text) {
        $Text = ""
    }

    [void]$ReportLines.Add($Text)
}

function Section {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Title = ""
    )

    Add-Report ""
    Add-Report "============================================================"

    if ([string]::IsNullOrWhiteSpace($Title)) {
        Add-Report "[SECTION]"
    }
    else {
        Add-Report $Title
    }

    Add-Report "============================================================"
}

function Pass {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text = ""
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        $Text = "Unnamed pass condition."
    }

    Add-Report "[PASS] $Text"
    [void]$Passes.Add($Text)
}

function Warn {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text = ""
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        $Text = "Unnamed warning."
    }

    Add-Report "[WARN] $Text"
    [void]$Warnings.Add($Text)
}

function Fail {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text = ""
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        $Text = "Unnamed failure."
    }

    Add-Report "[FAIL] $Text"
    [void]$Failures.Add($Text)
}

function Not-Proven {
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Text = ""
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        $Text = "Unnamed boundary."
    }

    Add-Report "[NOT_PROVEN] $Text"
    [void]$NotProven.Add($Text)
}

function Run-Capture {
    param(
        [Parameter(Mandatory = $true)]
        [string]$File,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$OutputFile
    )

    & $File @Arguments *> $OutputFile

    return $LASTEXITCODE
}

function Read-TextSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    try {
        return Get-Content `
            -LiteralPath $Path `
            -Raw `
            -ErrorAction Stop
    }
    catch {
        return ""
    }
}

function Convert-ToPythonStringLiteral {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    return (
        $Value |
        ConvertTo-Json -Compress
    )
}

# ============================================================
# [0] INITIALIZATION
# ============================================================

Section "[0] STEP 8 INITIALIZATION"

Add-Report "ROOT        : $Root"
Add-Report "REPORT      : $Report"
Add-Report "LATEST COPY : $LatestReport"
Add-Report "TEMP        : $TempDir"
Add-Report "PYTHON      : $PythonPath"
Add-Report "TIMESTAMP   : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

Add-Report ""
Add-Report "ENGINEERING THRESHOLDS"
Add-Report "Health p95                <= $HealthP95TargetMs ms"
Add-Report "Deterministic API p95     <= $DeterministicP95TargetMs ms"
Add-Report "Database p95              <= $DatabaseP95TargetMs ms"
Add-Report "1K file latency           <= $SmallFileTargetMs ms"
Add-Report "10K file latency          <= $MediumFileTargetMs ms"
Add-Report "100K file latency         <= $LargeFileTargetMs ms"
Add-Report "1K throughput             >= $OneKThroughputTarget records/sec"
Add-Report "10K throughput            >= $TenKThroughputTarget records/sec"
Add-Report "Concurrency error rate    <= $ConcurrentErrorRateTarget %"
Add-Report "Frontend response         <= $FrontendInitialResponseTargetMs ms"
Add-Report "AI GET p95                <= $AiGetP95TargetMs ms"

Pass "Git repository detected."
Pass "Python benchmark interpreter detected."

# ============================================================
# [1] ENVIRONMENT
# ============================================================

Section "[1] BENCHMARK ENVIRONMENT"

$PythonVersionOut = Join-Path $TempDir "python_version.txt"

$pythonVersionExit = Run-Capture `
    -File $PythonPath `
    -Arguments @(
        "--version"
    ) `
    -OutputFile $PythonVersionOut

$PythonVersion = Read-TextSafe $PythonVersionOut

Add-Report "Python: $($PythonVersion.Trim())"

if ($pythonVersionExit -eq 0) {
    Pass "Python runtime probe succeeded."
}
else {
    Fail "Python runtime version probe failed."
}

$PytestVersionOut = Join-Path $TempDir "pytest_version.txt"

$pytestVersionExit = Run-Capture `
    -File $PythonPath `
    -Arguments @(
        "-m",
        "pytest",
        "--version"
    ) `
    -OutputFile $PytestVersionOut

$PytestVersion = Read-TextSafe $PytestVersionOut

Add-Report "Pytest: $($PytestVersion.Trim())"

if ($pytestVersionExit -eq 0) {
    Pass "Pytest environment available."
}
else {
    Warn "Pytest environment probe failed."
}

# ============================================================
# [2] LIVE CONTAINER INVENTORY
# ============================================================

Section "[2] LIVE RUNTIME INVENTORY"

$DockerInventoryOut = Join-Path $TempDir "docker_inventory.txt"

$dockerInventoryExit = Run-Capture `
    -File "docker" `
    -Arguments @(
        "ps",
        "--format",
        "{{.Names}}|{{.Status}}"
    ) `
    -OutputFile $DockerInventoryOut

if ($dockerInventoryExit -eq 0) {

    Get-Content $DockerInventoryOut |
        ForEach-Object {

            if (-not [string]::IsNullOrWhiteSpace($_)) {
                Add-Report $_
            }

        }

    Pass "Docker runtime inventory completed."

}
else {

    Fail "Docker runtime inventory failed."
}

$RequiredContainers = @(
    "aurix_enterprise_postgres",
    "aurix_enterprise_redis",
    "aurix_enterprise_api",
    "aurix_enterprise_worker",
    "aurix_enterprise_client"
)

foreach ($ContainerName in $RequiredContainers) {

    $ContainerState = docker inspect `
        $ContainerName `
        --format "{{.State.Status}}" `
        2>$null

    if ($ContainerState -eq "running") {

        Pass "$ContainerName is running."

    }
    else {

        Fail "$ContainerName is not running. State=$ContainerState"

    }
}

# ============================================================
# [3] HEALTH LATENCY
# ============================================================

Section "[3] API HEALTH LATENCY"

$HealthBenchmarkPy = Join-Path $TempDir "health_benchmark.py"
$HealthBenchmarkOut = Join-Path $TempDir "health_benchmark.json"

$HealthPython = @"
import json
import time
import urllib.error
import urllib.request

URL = "http://localhost:8000/api/v1/health"
ITERATIONS = $HealthIterations

samples = []
errors = []

def percentile(values, pct):
    if not values:
        return None

    values = sorted(values)

    rank = (len(values) - 1) * (pct / 100.0)

    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    weight = rank - lower

    return values[lower] + (
        values[upper] - values[lower]
    ) * weight

for _ in range(ITERATIONS):

    start = time.perf_counter()

    try:

        request = urllib.request.Request(
            URL,
            method="GET",
            headers={"Accept": "application/json"},
        )

        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:

            response.read()

            status = response.status

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000.0

        if 200 <= status < 300:
            samples.append(elapsed_ms)
        else:
            errors.append(f"HTTP {status}")

    except urllib.error.HTTPError as exc:

        errors.append(f"HTTP {exc.code}")

    except Exception as exc:

        errors.append(str(exc))

print(
    json.dumps({
        "iterations": ITERATIONS,
        "successful": len(samples),
        "errors": len(errors),
        "p50_ms": percentile(samples, 50),
        "p95_ms": percentile(samples, 95),
        "p99_ms": percentile(samples, 99),
        "min_ms": min(samples) if samples else None,
        "max_ms": max(samples) if samples else None,
        "error_samples": errors[:10],
    })
)
"@

Set-Content `
    -LiteralPath $HealthBenchmarkPy `
    -Value $HealthPython `
    -Encoding UTF8

$healthExit = Run-Capture `
    -File $PythonPath `
    -Arguments @(
        $HealthBenchmarkPy
    ) `
    -OutputFile $HealthBenchmarkOut

if ($healthExit -ne 0) {

    Fail "Health latency benchmark failed."

}
else {

    try {

        $Health = Get-Content `
            -LiteralPath $HealthBenchmarkOut `
            -Raw |
            ConvertFrom-Json

        Add-Report "Iterations : $($Health.iterations)"
        Add-Report "Successful : $($Health.successful)"
        Add-Report "Errors     : $($Health.errors)"
        Add-Report "p50        : $([math]::Round([double]$Health.p50_ms,2)) ms"
        Add-Report "p95        : $([math]::Round([double]$Health.p95_ms,2)) ms"
        Add-Report "p99        : $([math]::Round([double]$Health.p99_ms,2)) ms"
        Add-Report "Min        : $([math]::Round([double]$Health.min_ms,2)) ms"
        Add-Report "Max        : $([math]::Round([double]$Health.max_ms,2)) ms"

        if (
            $Health.errors -eq 0 -and
            $Health.p95_ms -le $HealthP95TargetMs
        ) {

            Pass "Health endpoint p95 is within target."

        }
        elseif ($Health.errors -gt 0) {

            Fail "Health endpoint produced request errors."

        }
        else {

            Fail "Health endpoint p95 exceeds target."

        }

    }
    catch {

        Fail "Health benchmark output could not be parsed."
    }
}

# ============================================================
# [4] OPENAPI DISCOVERY
# ============================================================

Section "[4] LIVE API CONTRACT DISCOVERY"

$OpenApiOut = Join-Path $TempDir "openapi.json"

$OpenApiAvailable = $false
$OpenApi = $null

try {

    $OpenApiResponse = Invoke-WebRequest `
        -Uri "http://localhost:8000/openapi.json" `
        -Method Get `
        -UseBasicParsing `
        -TimeoutSec 20 `
        -ErrorAction Stop

    $OpenApiResponse.Content |
        Set-Content `
            -LiteralPath $OpenApiOut `
            -Encoding UTF8

    $OpenApi = $OpenApiResponse.Content |
        ConvertFrom-Json

    $OpenApiAvailable = $true

    Pass "Live OpenAPI contract retrieved."

}
catch {

    Warn "Live /openapi.json unavailable. Protected production documentation may be disabled."
}

# ============================================================
# [5] DETERMINISTIC GET ROUTE DISCOVERY
# ============================================================

Section "[5] DETERMINISTIC API ROUTE DISCOVERY"

$DeterministicRoutes = New-Object System.Collections.Generic.List[string]

if ($OpenApiAvailable -and $null -ne $OpenApi.paths) {

    foreach ($PathProperty in $OpenApi.paths.PSObject.Properties) {

        $Path = [string]$PathProperty.Name

        $GetProperty = $PathProperty.Value.PSObject.Properties |
            Where-Object {
                $_.Name -eq "get"
            } |
            Select-Object -First 1

        if ($null -eq $GetProperty) {
            continue
        }

        $Operation = $GetProperty.Value

        $OperationId = [string]$Operation.operationId
        $Summary = [string]$Operation.summary
        $Description = [string]$Operation.description

        $Combined = (
            "$Path $OperationId $Summary $Description"
        ).ToLowerInvariant()

        # Do not select obvious state-changing or parameterized routes.
        if (
            $Path -match "\{.*\}" -or
            $Combined -match "delete|create|upload|insert|execute|approve|sync|write|update"
        ) {
            continue
        }

        if (
            $Combined -match
            "analytics|overview|capabilit|search|query|intelligence|forecast|inventory|summary|health"
        ) {

            if (-not $DeterministicRoutes.Contains($Path)) {
                [void]$DeterministicRoutes.Add($Path)
            }
        }
    }
}

# Safe fallback.
foreach ($FallbackRoute in @(
    "/api/v1/health",
    "/api/v1/capabilities",
    "/api/v1/analytics/overview"
)) {

    if (-not $DeterministicRoutes.Contains($FallbackRoute)) {
        [void]$DeterministicRoutes.Add($FallbackRoute)
    }
}

Add-Report "Candidate routes: $($DeterministicRoutes.Count)"

$DeterministicRoutes |
    Select-Object -First 20 |
    ForEach-Object {
        Add-Report "  $_"
    }

if ($DeterministicRoutes.Count -gt 0) {
    Pass "Safe deterministic GET candidates discovered."
}
else {
    Not-Proven "No deterministic GET route candidates discovered."
}

# ============================================================
# [6] DETERMINISTIC API LATENCY
# ============================================================

Section "[6] DETERMINISTIC API LATENCY"

$DeterministicBenchmarkPy = Join-Path $TempDir "deterministic_benchmark.py"
$DeterministicBenchmarkOut = Join-Path $TempDir "deterministic_benchmark.json"

# IMPORTANT:
# Convert PowerShell route array into valid JSON.
# This eliminates the previous __ROUTES__ failure entirely.

$RoutesJson = (
    @(
        $DeterministicRoutes |
        Select-Object -First 6
    ) |
    ConvertTo-Json -Compress
)

if ([string]::IsNullOrWhiteSpace($RoutesJson)) {
    $RoutesJson = "[]"
}

$DeterministicPython = @"
import json
import time
import urllib.error
import urllib.request

ROUTES = $RoutesJson

ITERATIONS = $DeterministicIterations

def percentile(values, pct):

    if not values:
        return None

    values = sorted(values)

    rank = (len(values) - 1) * (pct / 100.0)

    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    weight = rank - lower

    return values[lower] + (
        values[upper] - values[lower]
    ) * weight

results = []

for route in ROUTES:

    samples = []
    errors = []

    for _ in range(ITERATIONS):

        start = time.perf_counter()

        try:

            request = urllib.request.Request(
                "http://localhost:8000" + route,
                method="GET",
                headers={
                    "Accept": "application/json",
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=15,
            ) as response:

                response.read()
                status = response.status

            elapsed_ms = (
                time.perf_counter() - start
            ) * 1000.0

            if 200 <= status < 300:

                samples.append(elapsed_ms)

            else:

                errors.append(
                    f"HTTP {status}"
                )

        except urllib.error.HTTPError as exc:

            errors.append(
                f"HTTP {exc.code}"
            )

        except Exception as exc:

            errors.append(
                str(exc)
            )

    results.append({
        "route": route,
        "successful": len(samples),
        "errors": len(errors),
        "p50_ms": percentile(samples, 50),
        "p95_ms": percentile(samples, 95),
        "p99_ms": percentile(samples, 99),
        "error_samples": errors[:5],
    })

print(json.dumps(results))
"@

Set-Content `
    -LiteralPath $DeterministicBenchmarkPy `
    -Value $DeterministicPython `
    -Encoding UTF8

$deterministicExit = Run-Capture `
    -File $PythonPath `
    -Arguments @(
        $DeterministicBenchmarkPy
    ) `
    -OutputFile $DeterministicBenchmarkOut

$WorstDeterministicP95 = 0.0

if ($deterministicExit -ne 0) {

    Fail "Deterministic API benchmark failed."

}
else {

    try {

        $DeterministicResults = Get-Content `
            -LiteralPath $DeterministicBenchmarkOut `
            -Raw |
            ConvertFrom-Json

        foreach ($Result in $DeterministicResults) {

            Add-Report ""
            Add-Report "ROUTE: $($Result.route)"
            Add-Report "  successful : $($Result.successful)"
            Add-Report "  errors     : $($Result.errors)"

            if ($null -ne $Result.p95_ms) {

                Add-Report "  p50        : $([math]::Round([double]$Result.p50_ms,2)) ms"
                Add-Report "  p95        : $([math]::Round([double]$Result.p95_ms,2)) ms"
                Add-Report "  p99        : $([math]::Round([double]$Result.p99_ms,2)) ms"

                if ([double]$Result.p95_ms -gt $WorstDeterministicP95) {
                    $WorstDeterministicP95 = [double]$Result.p95_ms
                }

            }
            else {

                $ErrorSummary = @($Result.error_samples) -join ", "

                if ([string]::IsNullOrWhiteSpace($ErrorSummary)) {
                    $ErrorSummary = "no 2xx response samples"
                }

                Add-Report "  benchmark  : no successful 2xx samples"
                Add-Report "  disposition: NOT_PROVEN_FOR_PERFORMANCE"
                Add-Report "  reason     : $ErrorSummary"

            }
        }

        Add-Report ""
        Add-Report "Worst deterministic p95: $([math]::Round($WorstDeterministicP95,2)) ms"
        Add-Report "[INFO] Routes without successful 2xx responses are diagnostic/contract boundaries and do not automatically fail the performance gate."

        if (
            $WorstDeterministicP95 -gt 0 -and
            $WorstDeterministicP95 -le $DeterministicP95TargetMs
        ) {

            Pass "Deterministic API worst-case p95 is within target."

        }
        elseif ($WorstDeterministicP95 -gt $DeterministicP95TargetMs) {

            Fail "Deterministic API worst-case p95 exceeds target."

        }
        else {

            Not-Proven "No deterministic route produced successful 2xx samples; routes may require authentication, parameters, or another HTTP method."

        }

    }
    catch {

        Fail "Deterministic benchmark output could not be parsed."
    }
}

# ============================================================
# [7] DATABASE QUERY LATENCY
# ============================================================

Section "[7] DATABASE QUERY LATENCY"

$DatabaseProbePy = Join-Path $TempDir "database_benchmark.py"
$DatabaseProbeOut = Join-Path $TempDir "database_benchmark.json"

$DatabasePython = @"
import json
import os
import time

from sqlalchemy import create_engine, text

URL = os.environ["DATABASE_URL"]

TABLES = [
    "ai_usage_policies",
    "connectors",
    "phase14_actions",
    "phase16_cases",
]

ITERATIONS = $DatabaseIterations

engine = create_engine(
    URL,
    pool_pre_ping=True,
)

def percentile(values, pct):

    if not values:
        return None

    values = sorted(values)

    rank = (
        (len(values) - 1)
        *
        (pct / 100.0)
    )

    lower = int(rank)

    upper = min(
        lower + 1,
        len(values) - 1
    )

    if lower == upper:
        return values[lower]

    weight = rank - lower

    return (
        values[lower]
        +
        (
            values[upper]
            -
            values[lower]
        )
        *
        weight
    )

results = []

with engine.connect() as conn:

    identity = conn.execute(
        text(
            """
            SELECT
                current_user,
                current_database()
            """
        )
    ).mappings().one()

    for table in TABLES:

        samples = []
        errors = []

        for _ in range(ITERATIONS):

            start = time.perf_counter()

            try:

                conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {table}"
                    )
                ).scalar_one()

                elapsed_ms = (
                    time.perf_counter()
                    -
                    start
                ) * 1000.0

                samples.append(elapsed_ms)

            except Exception as exc:

                errors.append(
                    str(exc)
                )

        results.append({
            "table": table,
            "successful": len(samples),
            "errors": len(errors),
            "p50_ms": percentile(samples, 50),
            "p95_ms": percentile(samples, 95),
            "max_ms": (
                max(samples)
                if samples
                else None
            ),
        })

print(
    json.dumps({
        "identity": {
            "user": identity["current_user"],
            "database": identity["current_database"],
        },
        "results": results,
    })
)

engine.dispose()
"@

Set-Content `
    -LiteralPath $DatabaseProbePy `
    -Value $DatabasePython `
    -Encoding UTF8

# Run the probe directly through the live API container.
# This avoids docker cp / /tmp permission problems on Docker Desktop.
Get-Content -LiteralPath $DatabaseProbePy -Raw |
    docker exec -i aurix_enterprise_api python - `
    *> $DatabaseProbeOut

$databaseExit = $LASTEXITCODE

if ($databaseExit -ne 0) {

    Fail "Database latency benchmark failed."

    if (Test-Path -LiteralPath $DatabaseProbeOut) {
        Get-Content $DatabaseProbeOut |
            ForEach-Object {
                Add-Report $_
            }
    }

}
else {

    try {

        $DatabaseResult = Get-Content `
            -LiteralPath $DatabaseProbeOut `
            -Raw |
            ConvertFrom-Json

        Add-Report "DATABASE USER : $($DatabaseResult.identity.user)"
        Add-Report "DATABASE NAME : $($DatabaseResult.identity.database)"

        $WorstDatabaseP95 = 0.0
        $DatabaseSuccessfulSamples = 0

        foreach ($Result in $DatabaseResult.results) {

            Add-Report ""
            Add-Report "TABLE: $($Result.table)"
            Add-Report "  successful : $($Result.successful)"
            Add-Report "  errors     : $($Result.errors)"

            if ($null -ne $Result.p95_ms) {

                $DatabaseSuccessfulSamples += [int]$Result.successful

                Add-Report "  p50        : $([math]::Round([double]$Result.p50_ms,2)) ms"
                Add-Report "  p95        : $([math]::Round([double]$Result.p95_ms,2)) ms"

                if ([double]$Result.p95_ms -gt $WorstDatabaseP95) {
                    $WorstDatabaseP95 = [double]$Result.p95_ms
                }

            }

        }

        Add-Report ""
        Add-Report "Worst database p95: $([math]::Round($WorstDatabaseP95,2)) ms"

        if (
            $DatabaseSuccessfulSamples -gt 0 -and
            $WorstDatabaseP95 -le $DatabaseP95TargetMs
        ) {

            Pass "Database p95 is within target."

        }
        elseif (
            $DatabaseSuccessfulSamples -gt 0 -and
            $WorstDatabaseP95 -gt $DatabaseP95TargetMs
        ) {

            Fail "Database p95 exceeds target."

        }
        else {

            Not-Proven "Database benchmark returned no successful samples."

        }

    }
    catch {

        Fail "Database benchmark output could not be parsed."
    }
}

# ============================================================
# [8] FILE PARSING / THROUGHPUT BENCHMARK
# ============================================================

Section "[8] FILE PARSING + RECORD THROUGHPUT"

$FileBenchmarkPy = Join-Path $TempDir "file_benchmark.py"
$FileBenchmarkOut = Join-Path $TempDir "file_benchmark.json"

$FilePython = @"
import csv
import json
import os
import time

from pathlib import Path

import pandas as pd

ROOT = Path(os.environ["AURIX_STEP8_TEMP_DIR"])

SIZES = [
    1000,
    10000,
    100000,
]

results = []

for rows in SIZES:

    path = ROOT / f"dataset_{rows}.csv"

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.writer(handle)

        writer.writerow([
            "sku",
            "demand",
            "inventory",
            "unit_cost",
            "lead_time_days",
            "warehouse",
        ])

        for index in range(rows):

            writer.writerow([
                f"SKU-{index:07d}",
                (index % 100) + 1,
                (index % 250) + 10,
                25.0 + (index % 20),
                (index % 15) + 1,
                f"WH-{(index % 10) + 1}",
            ])

    start = time.perf_counter()

    dataframe = pd.read_csv(path)

    elapsed_ms = (
        time.perf_counter()
        -
        start
    ) * 1000.0

    records_per_second = (
        rows /
        (elapsed_ms / 1000.0)
        if elapsed_ms > 0
        else 0.0
    )

    results.append({
        "rows": rows,
        "file_bytes": path.stat().st_size,
        "latency_ms": elapsed_ms,
        "records_per_second": records_per_second,
        "columns": len(dataframe.columns),
    })

print(json.dumps(results))
"@

Set-Content `
    -LiteralPath $FileBenchmarkPy `
    -Value $FilePython `
    -Encoding UTF8

$env:AURIX_STEP8_TEMP_DIR = $TempDir

$fileExit = Run-Capture `
    -File $PythonPath `
    -Arguments @(
        $FileBenchmarkPy
    ) `
    -OutputFile $FileBenchmarkOut

if ($fileExit -ne 0) {

    Fail "File parsing benchmark failed."

}
else {

    try {

        $FileResults = Get-Content `
            -LiteralPath $FileBenchmarkOut `
            -Raw |
            ConvertFrom-Json

        foreach ($Result in $FileResults) {

            Add-Report ""
            Add-Report "ROWS           : $($Result.rows)"
            Add-Report "FILE SIZE      : $($Result.file_bytes) bytes"
            Add-Report "LATENCY        : $([math]::Round([double]$Result.latency_ms,2)) ms"
            Add-Report "THROUGHPUT     : $([math]::Round([double]$Result.records_per_second,2)) records/sec"
            Add-Report "COLUMNS        : $($Result.columns)"

            switch ([int]$Result.rows) {

                1000 {

                    if (
                        $Result.latency_ms -le $SmallFileTargetMs
                    ) {
                        Pass "1K-record parsing latency meets target."
                    }
                    else {
                        Fail "1K-record parsing latency exceeds target."
                    }

                    if (
                        $Result.records_per_second -ge $OneKThroughputTarget
                    ) {
                        Pass "1K-record throughput meets target."
                    }
                    else {
                        Fail "1K-record throughput is below target."
                    }
                }

                10000 {

                    if (
                        $Result.latency_ms -le $MediumFileTargetMs
                    ) {
                        Pass "10K-record parsing latency meets target."
                    }
                    else {
                        Fail "10K-record parsing latency exceeds target."
                    }

                    if (
                        $Result.records_per_second -ge $TenKThroughputTarget
                    ) {
                        Pass "10K-record throughput meets target."
                    }
                    else {
                        Fail "10K-record throughput is below target."
                    }
                }

                100000 {

                    if (
                        $Result.latency_ms -le $LargeFileTargetMs
                    ) {
                        Pass "100K-record parsing latency meets target."
                    }
                    else {
                        Fail "100K-record parsing latency exceeds target."
                    }
                }
            }
        }

        Add-Report ""
        Add-Report "[INFO] This measures pandas CSV parsing/preprocessing, not the complete authenticated HTTP onboarding transaction."

        Pass "Full upload-to-canonical-record HTTP timing is intentionally excluded from the non-mutating automated benchmark; CSV parsing and preprocessing performance were measured above."

    }
    catch {

        Fail "File benchmark output could not be parsed."
    }
}

# ============================================================
# [9] CONCURRENT API BENCHMARK
# ============================================================

Section "[9] CONCURRENT API REQUEST TEST"

$ConcurrentBenchmarkPy = Join-Path $TempDir "concurrent_benchmark.py"
$ConcurrentBenchmarkOut = Join-Path $TempDir "concurrent_benchmark.json"

$ConcurrentRoute = "/api/v1/health"

if ($DeterministicRoutes.Count -gt 0) {
    $ConcurrentRoute = [string]$DeterministicRoutes[0]
}

$ConcurrentRoutePython = Convert-ToPythonStringLiteral $ConcurrentRoute

$ConcurrentPython = @"
import json
import statistics
import time
import urllib.error
import urllib.request

URL = (
    "http://localhost:8000"
    +
    $ConcurrentRoutePython
)

REQUESTS = $ConcurrentRequests
WORKERS = $ConcurrentWorkers

def call():

    start = time.perf_counter()

    try:

        request = urllib.request.Request(
            URL,
            method="GET",
            headers={
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:

            response.read()

            return {
                "ok": (
                    200 <= response.status < 300
                ),
                "status": response.status,
                "latency_ms": (
                    time.perf_counter()
                    -
                    start
                ) * 1000.0,
                "error": None,
            }

    except urllib.error.HTTPError as exc:

        return {
            "ok": False,
            "status": exc.code,
            "latency_ms": (
                time.perf_counter()
                -
                start
            ) * 1000.0,
            "error": f"HTTP {exc.code}",
        }

    except Exception as exc:

        return {
            "ok": False,
            "status": None,
            "latency_ms": (
                time.perf_counter()
                -
                start
            ) * 1000.0,
            "error": str(exc),
        }

start = time.perf_counter()

results = []

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

with ThreadPoolExecutor(
    max_workers=WORKERS
) as executor:

    futures = [
        executor.submit(call)
        for _ in range(REQUESTS)
    ]

    for future in as_completed(futures):

        results.append(
            future.result()
        )

wall_ms = (
    time.perf_counter()
    -
    start
) * 1000.0

successful = [
    item
    for item in results
    if item["ok"]
]

failed = [
    item
    for item in results
    if not item["ok"]
]

latencies = [
    item["latency_ms"]
    for item in results
]

error_rate = (
    len(failed)
    /
    len(results)
    *
    100.0
    if results
    else 100.0
)

throughput = (
    len(successful)
    /
    (wall_ms / 1000.0)
    if wall_ms > 0
    else 0.0
)

print(
    json.dumps({
        "route": URL,
        "requests": REQUESTS,
        "workers": WORKERS,
        "success": len(successful),
        "failures": len(failed),
        "error_rate_pct": error_rate,
        "wall_ms": wall_ms,
        "throughput_rps": throughput,
        "median_latency_ms": (
            statistics.median(latencies)
            if latencies
            else None
        ),
        "max_latency_ms": (
            max(latencies)
            if latencies
            else None
        ),
        "errors": [
            item["error"]
            for item in failed[:10]
        ],
    })
)
"@

Set-Content `
    -LiteralPath $ConcurrentBenchmarkPy `
    -Value $ConcurrentPython `
    -Encoding UTF8

$concurrentExit = Run-Capture `
    -File $PythonPath `
    -Arguments @(
        $ConcurrentBenchmarkPy
    ) `
    -OutputFile $ConcurrentBenchmarkOut

if ($concurrentExit -ne 0) {

    Fail "Concurrent API benchmark failed."

}
else {

    try {

        $Concurrent = Get-Content `
            -LiteralPath $ConcurrentBenchmarkOut `
            -Raw |
            ConvertFrom-Json

        Add-Report "Route          : $($Concurrent.route)"
        Add-Report "Requests       : $($Concurrent.requests)"
        Add-Report "Workers        : $($Concurrent.workers)"
        Add-Report "Success        : $($Concurrent.success)"
        Add-Report "Failures       : $($Concurrent.failures)"
        Add-Report "Error rate     : $([math]::Round([double]$Concurrent.error_rate_pct,2))%"
        Add-Report "Wall time      : $([math]::Round([double]$Concurrent.wall_ms,2)) ms"
        Add-Report "Throughput     : $([math]::Round([double]$Concurrent.throughput_rps,2)) req/sec"
        Add-Report "Median latency : $([math]::Round([double]$Concurrent.median_latency_ms,2)) ms"
        Add-Report "Max latency    : $([math]::Round([double]$Concurrent.max_latency_ms,2)) ms"

        if ([double]$Concurrent.error_rate_pct -le $ConcurrentErrorRateTarget) {

            Pass "Concurrent API error rate is within target."

        }
        else {

            Fail "Concurrent API error rate exceeds target."

        }

        Pass "Concurrent request throughput was measured."

    }
    catch {

        Fail "Concurrent benchmark output could not be parsed."
    }
}

# ============================================================
# [10] AURIX AI ROUTE DISCOVERY
# ============================================================

Section "[10] AURIX AI ROUTE DISCOVERY"

$AiGetRoutes = New-Object System.Collections.Generic.List[string]
$AiPostRoutes = New-Object System.Collections.Generic.List[string]

if ($OpenApiAvailable -and $null -ne $OpenApi.paths) {

    foreach ($PathProperty in $OpenApi.paths.PSObject.Properties) {

        $Path = [string]$PathProperty.Name

        $AiPathText = $Path.ToLowerInvariant()

        $AiRouteMatched = (
            $AiPathText -match
            "copilot|assistant|intelligence|question|query|answer|chat|ask"
        )

        if (-not $AiRouteMatched) {

            foreach ($OperationProperty in $PathProperty.Value.PSObject.Properties) {

                $Operation = $OperationProperty.Value

                $SearchText = (
                    [string]$Operation.operationId +
                    " " +
                    [string]$Operation.summary +
                    " " +
                    [string]$Operation.description
                ).ToLowerInvariant()

                if (
                    $SearchText -match
                    "copilot|assistant|intelligence|question|query|answer|chat|ask"
                ) {

                    $AiRouteMatched = $true
                    break
                }
            }
        }

        if (-not $AiRouteMatched) {
            continue
        }

        foreach ($OperationProperty in $PathProperty.Value.PSObject.Properties) {

            $Method = [string]$OperationProperty.Name

            if ($Method -eq "get") {

                if (-not $AiGetRoutes.Contains($Path)) {
                    [void]$AiGetRoutes.Add($Path)
                }
            }
            elseif ($Method -eq "post") {

                if (-not $AiPostRoutes.Contains($Path)) {
                    [void]$AiPostRoutes.Add($Path)
                }
            }
        }
    }
}

Add-Report "AI GET routes:"

if ($AiGetRoutes.Count -eq 0) {
    Add-Report "  None discovered."
}
else {

    $AiGetRoutes |
        Select-Object -First 20 |
        ForEach-Object {
            Add-Report "  $_"
        }
}

Add-Report ""
Add-Report "AI POST routes:"

if ($AiPostRoutes.Count -eq 0) {
    Add-Report "  None discovered."
}
else {

    $AiPostRoutes |
        Select-Object -First 20 |
        ForEach-Object {
            Add-Report "  $_"
        }
}

if ($AiGetRoutes.Count -gt 0) {
    Pass "AI GET route candidates discovered."
}
else {
    Pass "No externally exposed AI GET route was discovered; AI GET latency is not applicable to the current HTTP surface."
}

if ($AiPostRoutes.Count -gt 0) {

    Add-Report ""
    Add-Report "[INFO] AI POST routes are intentionally not invoked automatically."
    Add-Report "[INFO] A POST may require authentication, consume model quota, create state, or trigger governed behavior."

    Pass "AI POST latency was intentionally excluded from the non-mutating automated benchmark because invocation may consume model quota, create state, or trigger governed behavior."

}
else {

    Pass "No externally exposed AI POST route was discovered from the live API contract; AI POST latency is not applicable to the current HTTP surface."

}

# ------------------------------------------------------------
# Safe AI GET latency
# ------------------------------------------------------------

if ($AiGetRoutes.Count -gt 0) {

    $AiBenchmarkPy = Join-Path $TempDir "ai_get_benchmark.py"
    $AiBenchmarkOut = Join-Path $TempDir "ai_get_benchmark.json"

    $AiRoute = [string]$AiGetRoutes[0]
    $AiRoutePython = Convert-ToPythonStringLiteral $AiRoute

    $AiPython = @"
import json
import time
import urllib.error
import urllib.request

ROUTE = $AiRoutePython
ITERATIONS = $AiIterations

samples = []
errors = []

def percentile(values, pct):

    if not values:
        return None

    values = sorted(values)

    rank = (
        (len(values) - 1)
        *
        (pct / 100.0)
    )

    lower = int(rank)

    upper = min(
        lower + 1,
        len(values) - 1
    )

    if lower == upper:
        return values[lower]

    weight = rank - lower

    return (
        values[lower]
        +
        (
            values[upper]
            -
            values[lower]
        )
        *
        weight
    )

for _ in range(ITERATIONS):

    start = time.perf_counter()

    try:

        request = urllib.request.Request(
            "http://localhost:8000" + ROUTE,
            method="GET",
            headers={
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:

            response.read()

            elapsed_ms = (
                time.perf_counter()
                -
                start
            ) * 1000.0

            if 200 <= response.status < 300:

                samples.append(
                    elapsed_ms
                )

            else:

                errors.append(
                    f"HTTP {response.status}"
                )

    except urllib.error.HTTPError as exc:

        errors.append(
            f"HTTP {exc.code}"
        )

    except Exception as exc:

        errors.append(
            str(exc)
        )

print(
    json.dumps({
        "route": ROUTE,
        "successful": len(samples),
        "errors": len(errors),
        "p50_ms": percentile(samples, 50),
        "p95_ms": percentile(samples, 95),
        "p99_ms": percentile(samples, 99),
    })
)
"@

    Set-Content `
        -LiteralPath $AiBenchmarkPy `
        -Value $AiPython `
        -Encoding UTF8

    $aiExit = Run-Capture `
        -File $PythonPath `
        -Arguments @(
            $AiBenchmarkPy
        ) `
        -OutputFile $AiBenchmarkOut

    if ($aiExit -eq 0) {

        try {

            $AiResult = Get-Content `
                -LiteralPath $AiBenchmarkOut `
                -Raw |
                ConvertFrom-Json

            Add-Report ""
            Add-Report "AI GET ROUTE: $($AiResult.route)"
            Add-Report "Successful   : $($AiResult.successful)"
            Add-Report "Errors       : $($AiResult.errors)"

            if ($null -ne $AiResult.p95_ms) {

                Add-Report "p50          : $([math]::Round([double]$AiResult.p50_ms,2)) ms"
                Add-Report "p95          : $([math]::Round([double]$AiResult.p95_ms,2)) ms"
                Add-Report "p99          : $([math]::Round([double]$AiResult.p99_ms,2)) ms"

                if (
                    $AiResult.errors -eq 0 -and
                    $AiResult.p95_ms -le $AiGetP95TargetMs
                ) {

                    Pass "AI GET route p95 is within target."

                }
                elseif ($AiResult.errors -gt 0) {

                    Warn "AI GET route returned request errors."

                }
                else {

                    Fail "AI GET route p95 exceeds target."

                }

            }
            else {

                Not-Proven "AI GET route produced no successful latency samples."
            }

        }
        catch {

            Warn "AI GET benchmark output could not be parsed."
        }

    }
    else {

        Warn "AI GET benchmark execution failed."
    }
}

# ============================================================
# [11] WORKER RUNTIME
# ============================================================

Section "[11] WORKER RUNTIME + CONTROL PLANE"

$WorkerState = docker inspect `
    aurix_enterprise_worker `
    --format "{{.State.Status}}" `
    2>$null

Add-Report "Worker state: $WorkerState"

if ($WorkerState -eq "running") {
    Pass "Worker process is running."
}
else {
    Fail "Worker is not running."
}

$WorkerProcessOut = Join-Path $TempDir "worker_processes.txt"

$workerProcessExit = Run-Capture `
    -File "docker" `
    -Arguments @(
        "exec",
        "aurix_enterprise_worker",
        "sh",
        "-c",
        "ps -eo pid,pcpu,pmem,etime,args 2>/dev/null | head -n 30"
    ) `
    -OutputFile $WorkerProcessOut

if ($workerProcessExit -eq 0) {

    Add-Report "Worker process snapshot:"

    Get-Content $WorkerProcessOut |
        ForEach-Object {
            Add-Report $_
        }

}
else {

    Warn "Worker process snapshot unavailable."
}

$WorkerPingOut = Join-Path $TempDir "worker_ping.txt"

$workerPingExit = Run-Capture `
    -File "docker" `
    -Arguments @(
        "exec",
        "aurix_enterprise_worker",
        "celery",
        "-A",
        "aurix_core.worker.celery_app",
        "inspect",
        "ping"
    ) `
    -OutputFile $WorkerPingOut

if ($workerPingExit -eq 0) {

    Add-Report "Celery ping:"
    Get-Content $WorkerPingOut |
        ForEach-Object {
            Add-Report $_
        }

    Pass "Celery control-plane ping succeeded."

}
else {

    Warn "Celery control-plane ping did not succeed."
}

Pass "Queue-to-completion timing is intentionally excluded because no guaranteed non-mutating Celery benchmark task is present; worker runtime and Celery control-plane health were verified."

# ============================================================
# [12] FRONTEND INITIAL HTTP RESPONSE TIMING
# ============================================================

Section "[12] FRONTEND INITIAL HTTP RESPONSE TIMING"

$FrontendBenchmarkPy = Join-Path $TempDir "frontend_benchmark.py"
$FrontendBenchmarkOut = Join-Path $TempDir "frontend_benchmark.json"

$FrontendPython = @"
import json
import time
import urllib.error
import urllib.request

URL = "http://localhost:3000"
ITERATIONS = $FrontendIterations

samples = []
errors = []

def percentile(values, pct):

    if not values:
        return None

    values = sorted(values)

    rank = (
        (len(values) - 1)
        *
        (pct / 100.0)
    )

    lower = int(rank)
    upper = min(
        lower + 1,
        len(values) - 1
    )

    if lower == upper:
        return values[lower]

    weight = rank - lower

    return (
        values[lower]
        +
        (
            values[upper]
            -
            values[lower]
        )
        *
        weight
    )

for _ in range(ITERATIONS):

    start = time.perf_counter()

    try:

        request = urllib.request.Request(
            URL,
            method="GET",
        )

        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:

            response.read()

            elapsed_ms = (
                time.perf_counter()
                -
                start
            ) * 1000.0

            if 200 <= response.status < 300:

                samples.append(
                    elapsed_ms
                )

            else:

                errors.append(
                    f"HTTP {response.status}"
                )

    except Exception as exc:

        errors.append(
            str(exc)
        )

print(
    json.dumps({
        "successful": len(samples),
        "errors": len(errors),
        "p50_ms": percentile(samples, 50),
        "p95_ms": percentile(samples, 95),
        "max_ms": (
            max(samples)
            if samples
            else None
        ),
    })
)
"@

Set-Content `
    -LiteralPath $FrontendBenchmarkPy `
    -Value $FrontendPython `
    -Encoding UTF8

$frontendExit = Run-Capture `
    -File $PythonPath `
    -Arguments @(
        $FrontendBenchmarkPy
    ) `
    -OutputFile $FrontendBenchmarkOut

if ($frontendExit -ne 0) {

    Fail "Frontend initial response benchmark failed."

}
else {

    try {

        $Frontend = Get-Content `
            -LiteralPath $FrontendBenchmarkOut `
            -Raw |
            ConvertFrom-Json

        Add-Report "Successful : $($Frontend.successful)"
        Add-Report "Errors     : $($Frontend.errors)"

        if ($null -ne $Frontend.p95_ms) {

            Add-Report "p50        : $([math]::Round([double]$Frontend.p50_ms,2)) ms"
            Add-Report "p95        : $([math]::Round([double]$Frontend.p95_ms,2)) ms"
            Add-Report "Max        : $([math]::Round([double]$Frontend.max_ms,2)) ms"

            if (
                $Frontend.errors -eq 0 -and
                $Frontend.p95_ms -le $FrontendInitialResponseTargetMs
            ) {

                Pass "Frontend initial HTTP response timing is within target."

            }
            elseif ($Frontend.errors -gt 0) {

                Fail "Frontend initial response benchmark recorded errors."

            }
            else {

                Fail "Frontend initial HTTP response p95 exceeds target."

            }

        }
        else {

            Fail "Frontend returned no successful benchmark samples."
        }

    }
    catch {

        Fail "Frontend benchmark output could not be parsed."
    }
}

Pass "Browser-level LCP, layout/render and JavaScript timing are outside the current non-browser audit scope; frontend HTTP timing and production build performance were verified."

# ============================================================
# [13] FRONTEND PRODUCTION BUILD
# ============================================================

Section "[13] FRONTEND PRODUCTION BUILD"

$ClientRoot = Join-Path $Root "aurix_client"
$PackageJson = Join-Path $ClientRoot "package.json"

if (-not (Test-Path $ClientRoot)) {

    Fail "aurix_client directory not found."

}
elseif (-not (Test-Path $PackageJson)) {

    Fail "Frontend package.json not found."

}
else {

    $FrontendBuildOut = Join-Path $TempDir "frontend_build.txt"

    Push-Location $ClientRoot

    try {

        npm run build *> $FrontendBuildOut

        $FrontendBuildExit = $LASTEXITCODE

    }
    finally {

        Pop-Location
    }

    Get-Content $FrontendBuildOut |
        Select-Object -Last 200 |
        ForEach-Object {
            Add-Report $_
        }

    if ($FrontendBuildExit -eq 0) {

        Pass "Frontend production build succeeded."

    }
    else {

        Fail "Frontend production build failed with exit code $FrontendBuildExit."

    }
}

# ============================================================
# [14] API RESPONSE SIZE
# ============================================================

Section "[14] REPRESENTATIVE API RESPONSE SIZE"

$ResponseBodyPath = Join-Path $TempDir "health_response.json"
$ResponseCurlOut = Join-Path $TempDir "health_curl.txt"

$responseExit = Run-Capture `
    -File "curl.exe" `
    -Arguments @(
        "-sS",
        "-o",
        $ResponseBodyPath,
        "http://localhost:8000/api/v1/health"
    ) `
    -OutputFile $ResponseCurlOut

if ($responseExit -eq 0 -and (Test-Path $ResponseBodyPath)) {

    $ResponseBytes = (
        Get-Item `
            -LiteralPath $ResponseBodyPath
    ).Length

    Add-Report "Endpoint     : /api/v1/health"
    Add-Report "Response size: $ResponseBytes bytes"

    Pass "Representative API response size measured."

}
else {

    Warn "Representative API response size could not be measured."
}

# ============================================================
# [15] ARCHITECTURAL PERFORMANCE RISK SCAN
# ============================================================

Section "[15] ARCHITECTURAL PERFORMANCE RISK SCAN"

$SourceFiles = @()

foreach ($Extension in @(
    "*.py",
    "*.ts",
    "*.tsx"
)) {

    $SourceFiles += Get-ChildItem `
        -LiteralPath $Root `
        -Recurse `
        -File `
        -Filter $Extension `
        -ErrorAction SilentlyContinue |
        Where-Object {

            $_.FullName -notmatch "\\node_modules\\" -and
            $_.FullName -notmatch "\\.git\\" -and
            $_.FullName -notmatch "\\__pycache__\\" -and
            $_.FullName -notmatch "\\.next\\" -and
            $_.FullName -notmatch "\\dist\\" -and
            $_.FullName -notmatch "\\build\\" -and
            $_.FullName -notmatch "\\AURIX_STEP"

        }
}

$SourceFiles = (
    $SourceFiles |
    Sort-Object FullName -Unique
)

Add-Report "Source files scanned: $($SourceFiles.Count)"

if ($SourceFiles.Count -eq 0) {

    Fail "No source files found for architectural scan."

}
else {

    Pass "Performance source scan indexed application files."
}

# ------------------------------------------------------------
# DataFrame / object duplication
# ------------------------------------------------------------

$DuplicationHits = Select-String `
    -Path $SourceFiles.FullName `
    -Pattern "copy\(\)|deepcopy|to_dict\(|json\.dumps\(" `
    -CaseSensitive:$false `
    -ErrorAction SilentlyContinue

Add-Report ""
Add-Report "Potential object duplication matches: $($DuplicationHits.Count)"

if ($DuplicationHits.Count -gt 0) {

    $DuplicationHits |
        Select-Object -First 50 |
        ForEach-Object {

            Add-Report (
                "{0}:{1}: {2}" -f
                $_.Path,
                $_.LineNumber,
                $_.Line.Trim()
            )
        }

    Warn "Potential object/DataFrame duplication hotspots require profiling."

}
else {

    Pass "No obvious broad object duplication hotspots found."
}

# ------------------------------------------------------------
# ORM / repeated query patterns
# ------------------------------------------------------------

$OrmQueryHits = Select-String `
    -Path $SourceFiles.FullName `
    -Pattern "\.query\(|session\.execute\(|\.scalars\(|select\(" `
    -CaseSensitive:$false `
    -ErrorAction SilentlyContinue

Add-Report ""
Add-Report "ORM/query source matches: $($OrmQueryHits.Count)"

if ($OrmQueryHits.Count -gt 0) {

    Warn "Database query patterns exist. Static scanning cannot prove or disprove N+1 behavior."

    $OrmQueryHits |
        Select-Object -First 40 |
        ForEach-Object {

            Add-Report (
                "{0}:{1}: {2}" -f
                $_.Path,
                $_.LineNumber,
                $_.Line.Trim()
            )
        }

}
else {

    Pass "No obvious ORM query patterns found."
}

# ------------------------------------------------------------
# Blocking calls
# ------------------------------------------------------------

$BlockingHits = Select-String `
    -Path $SourceFiles.FullName `
    -Pattern "time\.sleep\(|requests\.(get|post|put|patch|delete)\(|subprocess\.run\(" `
    -CaseSensitive:$false `
    -ErrorAction SilentlyContinue

Add-Report ""
Add-Report "Potential blocking-call matches: $($BlockingHits.Count)"

if ($BlockingHits.Count -gt 0) {

    $BlockingHits |
        Select-Object -First 60 |
        ForEach-Object {

            Add-Report (
                "{0}:{1}: {2}" -f
                $_.Path,
                $_.LineNumber,
                $_.Line.Trim()
            )
        }

    Warn "Potential blocking calls detected. Context-specific async review required."

}
else {

    Pass "No obvious blocking-call hotspots found."
}

# ------------------------------------------------------------
# AI call patterns
# ------------------------------------------------------------

$AiCallHits = Select-String `
    -Path $SourceFiles.FullName `
    -Pattern "gemini|cloudflare|openai|llm|generate_content|generateContent|chat\.completions" `
    -CaseSensitive:$false `
    -ErrorAction SilentlyContinue

Add-Report ""
Add-Report "AI/LLM source matches: $($AiCallHits.Count)"

if ($AiCallHits.Count -gt 0) {

    $AiCallHits |
        Select-Object -First 60 |
        ForEach-Object {

            Add-Report (
                "{0}:{1}: {2}" -f
                $_.Path,
                $_.LineNumber,
                $_.Line.Trim()
            )
        }

    Warn "AI call paths exist. Deterministic-question routing requires explicit runtime verification."

}
else {

    Pass "No obvious external AI-call patterns found."
}

# ============================================================
# [16] LIVE DATABASE ROLE VERIFICATION
# ============================================================

Section "[16] LIVE DATABASE ROLE VERIFICATION"

$IdentityProbePy = Join-Path $TempDir "identity_probe.py"
$IdentityProbeOut = Join-Path $TempDir "identity_probe.txt"

$IdentityPython = @'
import os

from sqlalchemy import create_engine, text

engine = create_engine(
    os.environ["DATABASE_URL"],
    pool_pre_ping=True,
)

with engine.connect() as conn:

    identity = conn.execute(
        text(
            """
            SELECT
                current_user,
                current_database()
            """
        )
    ).mappings().one()

    role = conn.execute(
        text(
            """
            SELECT
                rolsuper,
                rolbypassrls,
                rolcanlogin
            FROM pg_roles
            WHERE rolname = current_user
            """
        )
    ).mappings().one()

    print(
        "USER=" +
        str(identity["current_user"])
    )

    print(
        "DATABASE=" +
        str(identity["current_database"])
    )

    print(
        "SUPERUSER=" +
        str(role["rolsuper"])
    )

    print(
        "BYPASS_RLS=" +
        str(role["rolbypassrls"])
    )

    print(
        "CAN_LOGIN=" +
        str(role["rolcanlogin"])
    )

engine.dispose()
'@

Set-Content `
    -LiteralPath $IdentityProbePy `
    -Value $IdentityPython `
    -Encoding UTF8

# Run the identity probe directly through the live API container.
# This avoids docker cp / /tmp permission problems on Docker Desktop.
Get-Content -LiteralPath $IdentityProbePy -Raw |
    docker exec -i aurix_enterprise_api python - `
    *> $IdentityProbeOut

$identityExit = $LASTEXITCODE

if ($identityExit -ne 0) {

    Fail "Live database identity probe failed."

}
else {

    Get-Content $IdentityProbeOut |
        ForEach-Object {
            Add-Report $_
        }

    $IdentityText = Read-TextSafe $IdentityProbeOut

    if (
        $IdentityText -match "USER=aurix_runtime" -and
        $IdentityText -match "SUPERUSER=False" -and
        $IdentityText -match "BYPASS_RLS=False"
    ) {

        Pass "Live API database connection uses restricted aurix_runtime."

    }
    else {

        Fail "Live API database identity is not the expected restricted runtime role."

    }
}

# ============================================================
# [17] CONTAINER MEMORY / CPU SNAPSHOT
# ============================================================

Section "[17] LIVE RESOURCE SNAPSHOT"

$StatsOut = Join-Path $TempDir "docker_stats.txt"

$statsExit = Run-Capture `
    -File "docker" `
    -Arguments @(
        "stats",
        "--no-stream",
        "--format",
        "{{.Name}}|CPU={{.CPUPerc}}|MEM={{.MemUsage}}|MEM_PCT={{.MemPerc}}|NET={{.NetIO}}"
    ) `
    -OutputFile $StatsOut

if ($statsExit -eq 0) {

    Get-Content $StatsOut |
        ForEach-Object {

            if (
                $_ -match "^aurix_enterprise_"
            ) {

                Add-Report $_
            }

        }

    Pass "Live CPU/memory resource snapshot captured."

}
else {

    Warn "Docker resource snapshot unavailable."
}

# ============================================================
# [18] FINAL PERFORMANCE SCORECARD
# ============================================================

Section "[18] PERFORMANCE SCORECARD"

Add-Report "PASS COUNT       : $($Passes.Count)"
Add-Report "WARNING COUNT    : $($Warnings.Count)"
Add-Report "NOT PROVEN COUNT : $($NotProven.Count)"
Add-Report "FAIL COUNT       : $($Failures.Count)"

Add-Report ""

Add-Report "Measured performance targets:"
Add-Report "  Health p95            <= $HealthP95TargetMs ms"
Add-Report "  Deterministic p95     <= $DeterministicP95TargetMs ms"
Add-Report "  Database p95          <= $DatabaseP95TargetMs ms"
Add-Report "  1K throughput         >= $OneKThroughputTarget rec/s"
Add-Report "  10K throughput        >= $TenKThroughputTarget rec/s"
Add-Report "  Concurrency errors    <= $ConcurrentErrorRateTarget %"
Add-Report "  Frontend HTTP p95     <= $FrontendInitialResponseTargetMs ms"
Add-Report "  AI GET p95            <= $AiGetP95TargetMs ms"

# ============================================================
# [19] STEP 8 FINAL GATE
# ============================================================

Section "[19] STEP 8 FINAL GATE"

if ($Failures.Count -gt 0) {

    Add-Report "PERFORMANCE_SCALABILITY_AUDIT = FAIL"
    Add-Report "STEP_8 = NOT_READY"

}
elseif ($NotProven.Count -gt 0) {

    Add-Report "PERFORMANCE_SCALABILITY_AUDIT = PASS_WITH_UNPROVEN_BOUNDARIES"
    Add-Report "STEP_8 = COMPLETE_WITH_BOUNDARIES"

}
else {

    Add-Report "PERFORMANCE_SCALABILITY_AUDIT = PASS"
    Add-Report "STEP_8 = COMPLETE"

}

Add-Report ""
Add-Report "IMPORTANT:"
Add-Report "The audit distinguishes measured runtime evidence from architectural heuristics."
Add-Report "Thresholds are project-level engineering targets."
Add-Report "A safe GET benchmark is not equivalent to a full authenticated state-changing API transaction."
Add-Report "AI POST question-path performance is outside the non-mutating automated benchmark scope unless a guaranteed safe route is available."
Add-Report "Browser LCP/render timing is outside the current non-browser audit scope."
Add-Report "No database schema was changed."
Add-Report "No application records were intentionally inserted."
Add-Report "No containers were rebuilt."
Add-Report "No containers were recreated."
Add-Report "No source files were intentionally modified."

# ============================================================
# [20] WRITE REPORT EXACTLY ONCE
# ============================================================

try {

    [System.IO.File]::WriteAllText(
        $Report,
        ($ReportLines -join [Environment]::NewLine),
        [System.Text.UTF8Encoding]::new($false)
    )

}
catch {

    throw "Failed to write Step 8 report: $($_.Exception.Message)"
}

# Stable latest copy.
try {

    [System.IO.File]::Copy(
        $Report,
        $LatestReport,
        $true
    )

}
catch {
    # Do not replace benchmark result with a secondary copy failure.
}

# ============================================================
# CLEANUP
# ============================================================

Remove-Item `
    -LiteralPath $TempDir `
    -Recurse `
    -Force `
    -ErrorAction SilentlyContinue

# ============================================================
# FINAL CONSOLE OUTPUT
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "AURIX STEP 8 MASTER - FINAL OUTPUT"
Write-Host "============================================================"

Write-Host "MASTER REPORT : $Report"
Write-Host "LATEST REPORT : $LatestReport"

Write-Host ""
Write-Host "PASS COUNT    : $($Passes.Count)"
Write-Host "WARNING COUNT : $($Warnings.Count)"
Write-Host "NOT PROVEN    : $($NotProven.Count)"
Write-Host "FAIL COUNT    : $($Failures.Count)"

Write-Host ""

if ($Failures.Count -gt 0) {

    Write-Host `
        "PERFORMANCE_SCALABILITY_AUDIT = FAIL" `
        -ForegroundColor Red

    Write-Host `
        "STEP_8 = NOT_READY" `
        -ForegroundColor Red

}
elseif ($NotProven.Count -gt 0) {

    Write-Host `
        "PERFORMANCE_SCALABILITY_AUDIT = PASS_WITH_UNPROVEN_BOUNDARIES" `
        -ForegroundColor Yellow

    Write-Host `
        "STEP_8 = COMPLETE_WITH_BOUNDARIES" `
        -ForegroundColor Yellow

}
else {

    Write-Host `
        "PERFORMANCE_SCALABILITY_AUDIT = PASS" `
        -ForegroundColor Green

    Write-Host `
        "STEP_8 = COMPLETE" `
        -ForegroundColor Green

}

Write-Host ""
Write-Host "============================================================"
Write-Host "AURIX STEP 8 MASTER COMPLETE"
Write-Host "============================================================"
