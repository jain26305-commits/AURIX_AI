$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path

$AuditRoot = Join-Path $Root "AURIX_STEP12"
New-Item -ItemType Directory -Force $AuditRoot | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ReportPath = Join-Path `
    $AuditRoot `
    "AURIX_STEP12_API_INTEGRATION_READINESS_$Timestamp.txt"

$LatestPath = Join-Path `
    $Root `
    "AURIX_STEP12_API_INTEGRATION_READINESS.txt"

$Failures = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]
$Passes   = New-Object System.Collections.Generic.List[string]

$ReportLines = New-Object System.Collections.Generic.List[string]

function Add-Report {
    param(
        [string]$Text
    )

    $ReportLines.Add($Text)
    Write-Host $Text
}

function Pass {
    param(
        [string]$Text
    )

    $Line = "[PASS] $Text"
    $Passes.Add($Text)
    Add-Report $Line
}

function Warn {
    param(
        [string]$Text
    )

    $Line = "[WARN] $Text"
    $Warnings.Add($Text)
    Add-Report $Line
}

function Fail {
    param(
        [string]$Text
    )

    $Line = "[FAIL] $Text"
    $Failures.Add($Text)
    Add-Report $Line
}

function Not-Proven {
    param(
        [string]$Text
    )

    $Line = "[NOT_PROVEN] $Text"
    $Warnings.Add($Text)
    Add-Report $Line
}

function Section {
    param(
        [string]$Title
    )

    Add-Report ""
    Add-Report "============================================================"
    Add-Report $Title
    Add-Report "============================================================"
}

function Run-Command {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$Label,
        [switch]$AllowFailure
    )

    Add-Report ""
    Add-Report ">>> $Label"

    $Output = @()

    try {
        $Output = & $FilePath @Arguments 2>&1

        foreach ($Line in $Output) {
            Add-Report ([string]$Line)
        }

        if ($LASTEXITCODE -ne 0) {
            if ($AllowFailure) {
                Warn "$Label returned exit code $LASTEXITCODE."
            }
            else {
                Fail "$Label returned exit code $LASTEXITCODE."
            }

            return $false
        }

        Pass "$Label succeeded."
        return $true
    }
    catch {
        if ($AllowFailure) {
            Warn "$Label failed: $($_.Exception.Message)"
        }
        else {
            Fail "$Label failed: $($_.Exception.Message)"
        }

        return $false
    }
}

function Get-ExistingTestFiles {
    param(
        [string[]]$Patterns
    )

    $Files = New-Object System.Collections.Generic.List[string]

    if (-not (Test-Path -LiteralPath (Join-Path $Root "tests"))) {
        return @()
    }

    foreach ($Pattern in $Patterns) {
        Get-ChildItem `
            -LiteralPath (Join-Path $Root "tests") `
            -Recurse `
            -File `
            -Filter "*.py" `
            -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -like $Pattern
            } |
            ForEach-Object {
                if (-not $Files.Contains($_.FullName)) {
                    $Files.Add($_.FullName)
                }
            }
    }

    return @($Files)
}

function Run-TestGroup {
    param(
        [string]$GroupName,
        [string[]]$Patterns
    )

    Section "[TEST GROUP] $GroupName"

    $Files = Get-ExistingTestFiles -Patterns $Patterns

    if ($Files.Count -eq 0) {
        Not-Proven "$GroupName has no dedicated test file discovered."
        return
    }

    foreach ($File in $Files) {
        Add-Report "TEST FILE: $File"

        $Result = & $Python `
            -m pytest `
            -q `
            $File 2>&1

        foreach ($Line in $Result) {
            Add-Report ([string]$Line)
        }

        if ($LASTEXITCODE -ne 0) {
            Fail "$GroupName failed in $([IO.Path]::GetFileName($File))."
        }
        else {
            Pass "$GroupName passed in $([IO.Path]::GetFileName($File))."
        }
    }
}

# ============================================================
# 0. INITIALIZATION
# ============================================================

Section "[0] STEP 12 INITIALIZATION"

$Python = $null

$PythonCandidates = @(
    "D:\Python-IDLE\python.exe",
    "python.exe"
)

foreach ($Candidate in $PythonCandidates) {

    try {

        if ($Candidate -eq "python.exe") {
            $Command = Get-Command python.exe -ErrorAction SilentlyContinue

            if ($Command) {
                $Python = $Command.Source
                break
            }
        }
        elseif (Test-Path -LiteralPath $Candidate) {
            $Python = $Candidate
            break
        }
    }
    catch {
    }
}

if ([string]::IsNullOrWhiteSpace($Python)) {
    throw "Python interpreter could not be located."
}

Add-Report "ROOT   : $Root"
Add-Report "PYTHON : $Python"
Add-Report "REPORT : $ReportPath"

# ============================================================
# 1. TOOLCHAIN
# ============================================================

# ============================================================
# Native Docker command helper
# ============================================================

$DockerComposeExe = "docker"

function Invoke-DockerInspectSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $PreviousErrorActionPreference = $ErrorActionPreference

    try {
        $ErrorActionPreference = "Continue"

        $Output = @(
            & docker inspect @Arguments 2>&1
        )

        $ExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }

    if ($ExitCode -ne 0) {
        throw "docker inspect failed with exit code $ExitCode."
    }

    return @($Output)
}
function Invoke-DockerExecSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $PreviousErrorActionPreference = $ErrorActionPreference

    try {
        # Native Docker/Alembic/Celery stderr must not become a
        # terminating NativeCommandError in Windows PowerShell.
        $ErrorActionPreference = "Continue"

        $Output = @(
            & docker exec @Arguments 2>&1
        )

        $ExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }

    foreach ($Line in $Output) {
        Add-Report ([string]$Line)
    }

    if ($ExitCode -ne 0) {
        throw "docker exec command failed with exit code $ExitCode."
    }

    return @($Output)
}
function Invoke-DockerComposeSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Add-Report ("DOCKER COMMAND: docker compose " + ($Arguments -join " "))

    $PreviousErrorActionPreference = $ErrorActionPreference

    try {
        # Windows PowerShell can convert native stderr into
        # NativeCommandError records when ErrorActionPreference=Stop.
        # Temporarily allow the command to complete normally.
        $ErrorActionPreference = "Continue"

        $Output = @(
            & $DockerComposeExe compose @Arguments 2>&1
        )

        $ExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }

    foreach ($Line in $Output) {
        Add-Report ([string]$Line)
    }

    if ($ExitCode -ne 0) {
        throw "docker compose command failed with exit code $ExitCode."
    }

    return @($Output)
}
Section "[1] TOOLCHAIN"

if (Get-Command docker.exe -ErrorAction SilentlyContinue) {
    Pass "Docker CLI available."
}
else {
    Fail "Docker CLI unavailable."
}

if (Get-Command git.exe -ErrorAction SilentlyContinue) {
    Pass "Git CLI available."
}
else {
    Fail "Git CLI unavailable."
}

if (Test-Path -LiteralPath (Join-Path $Root "docker-compose.yml")) {
    Pass "docker-compose.yml exists."
}
else {
    Fail "docker-compose.yml not found."
}

if (Test-Path -LiteralPath (Join-Path $Root ".env")) {
    Pass ".env exists."
}
else {
    Fail ".env not found."
}

# ============================================================
# 2. RELEASE IDENTITY
# ============================================================

Section "[2] RELEASE IDENTITY"

$GitSha = ""

try {
    $GitSha = (git rev-parse HEAD).Trim()

    if ($GitSha -match '^[0-9a-f]{40}$') {
        Pass "Git HEAD is a valid 40-character SHA."
        Add-Report "GIT_SHA=$GitSha"
    }
    else {
        Fail "Git HEAD is not a valid 40-character SHA."
    }
}
catch {
    Fail "Unable to determine Git HEAD."
}

try {

    $Tag = (git describe --tags --exact-match HEAD 2>$null).Trim()

    if (-not [string]::IsNullOrWhiteSpace($Tag)) {
        Add-Report "GIT_TAG=$Tag"
        Pass "HEAD has an exact release tag: $Tag"
    }
    else {
        Warn "HEAD has no exact release tag."
    }

}
catch {
    Warn "Git tag identity could not be determined."
}

# ============================================================
# 3. ENVIRONMENT CONTRACT
# ============================================================

Section "[3] ENVIRONMENT CONTRACT"

$EnvPath = Join-Path $Root ".env"

$RequiredEnv = @(
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "API_SECRET_KEY",
    "DATABASE_URL",
    "ARTIFACT_STORAGE_BACKEND",
    "ARTIFACT_STORAGE_BUCKET",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "RELEASE_COMMIT"
)

$EnvMap = @{}

foreach ($Line in Get-Content -LiteralPath $EnvPath) {

    if ($Line -match '^\s*([^#=\s]+)\s*=(.*)$') {
        $EnvMap[$Matches[1]] = $Matches[2]
    }
}

foreach ($Name in $RequiredEnv) {

    $Value = [string]$EnvMap[$Name]

    if ([string]::IsNullOrWhiteSpace($Value)) {
        Fail "$Name is missing from .env."
    }
    else {

        if ($Name -eq "API_SECRET_KEY") {
            Add-Report "API_SECRET_KEY_LENGTH=$($Value.Length)"

            if ($Value.Length -ge 32) {
                Pass "API_SECRET_KEY is present and >= 32 characters."
            }
            else {
                Fail "API_SECRET_KEY is shorter than 32 characters."
            }
        }
        elseif ($Name -eq "SUPABASE_SERVICE_ROLE_KEY") {
            Add-Report "SUPABASE_SERVICE_ROLE_KEY_LENGTH=$($Value.Length)"

            if ($Value.Length -gt 0) {
                Pass "Supabase service-role key is configured."
            }
            else {
                Fail "Supabase service-role key is empty."
            }
        }
        elseif ($Name -eq "SUPABASE_URL") {

            if ($Value -match '^https://[^/]+\.supabase\.co$') {
                Pass "SUPABASE_URL has expected project URL shape."
            }
            else {
                Warn "SUPABASE_URL does not match the normal Supabase project URL pattern."
            }
        }
        else {
            Pass "$Name is configured."
        }
    }
}

if ($EnvMap["ARTIFACT_STORAGE_BACKEND"] -ne "supabase") {
    Fail "Production artifact storage backend is not supabase."
}
else {
    Pass "Production artifact storage uses Supabase."
}

if ($EnvMap["ARTIFACT_STORAGE_BUCKET"] -ne "aurix-artifacts") {
    Warn "Artifact storage bucket differs from aurix-artifacts."
}
else {
    Pass "Artifact storage bucket is aurix-artifacts."
}

if ($EnvMap["RELEASE_COMMIT"] -eq $GitSha) {
    Pass ".env RELEASE_COMMIT matches Git HEAD."
}
else {
    Fail ".env RELEASE_COMMIT does not match Git HEAD."
}

# ============================================================
# 4. DOCKER COMPOSE RESOLUTION
# ============================================================

Section "[4] DOCKER COMPOSE RESOLUTION"
$ComposeConfig = Invoke-DockerComposeSafe @("config")
foreach ($Line in $ComposeConfig) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -ne 0) {
    Fail "docker compose config failed."
}
else {

    Pass "docker compose configuration is valid."

    $ComposeText = ($ComposeConfig -join "`n")

    $ComposeFalseValueChecks = @{
        "ENABLE_DOCS: false" = '(?m)^\s*ENABLE_DOCS:\s*["'']?false["'']?\s*$'
        "DEBUG: false"       = '(?m)^\s*DEBUG:\s*["'']?false["'']?\s*$'
    }

    foreach ($FalseContract in $ComposeFalseValueChecks.GetEnumerator()) {
        if ($ComposeText -match $FalseContract.Value) {
            Pass "Compose contract contains: $($FalseContract.Key)"
        }
        else {
            Fail "Compose contract is missing: $($FalseContract.Key)"
        }
    }
    foreach ($RequiredText in @(
        "ENVIRONMENT: production",


        "API_SECRET_KEY:",
        "DATABASE_URL:",
        "RELEASE_COMMIT:",
        "ARTIFACT_STORAGE_BACKEND: supabase",
        "ARTIFACT_STORAGE_BUCKET: aurix-artifacts",
        "SUPABASE_URL:",
        "SUPABASE_SERVICE_ROLE_KEY:"
    )) {

        if ($ComposeText -match [regex]::Escape($RequiredText)) {
            Pass "Compose contract contains: $RequiredText"
        }
        else {
            Fail "Compose contract is missing: $RequiredText"
        }
    }
}

# ============================================================
# 5. CLEAN DEPLOYMENT
# ============================================================

Section "[5] CLEAN DEPLOYMENT"

Add-Report "Stopping/removing current containers."
Add-Report "PostgreSQL named volume will NOT be deleted."

$DownOutput = Invoke-DockerComposeSafe @("down","--remove-orphans")

$DownExitCode = $LASTEXITCODE

if ($DownExitCode -ne 0) {
    Write-Host "[FAIL] docker compose down returned exit code $DownExitCode." -ForegroundColor Red

    $DownOutput |
        ForEach-Object {
            Write-Host ([string]$_)
        }

    throw "Clean deployment teardown failed."
}

foreach ($Line in $DownOutput) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -ne 0) {
    Fail "docker compose down failed."
}
else {
    Pass "Existing compose containers removed without deleting database volumes."
}

Add-Report ""
Add-Report "Building production services."

$BuildOutput = Invoke-DockerComposeSafe @("build","aurix-api","aurix-worker","aurix-client")

foreach ($Line in $BuildOutput) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -ne 0) {
    Fail "Production Docker image build failed."
}
else {
    Pass "Production Docker images built successfully."
}

Add-Report ""
Add-Report "Starting PostgreSQL and Redis."
$InfraOutput = Invoke-DockerComposeSafe @("up","-d","aurix-postgres","aurix-redis")
foreach ($Line in $InfraOutput) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -ne 0) {
    Fail "PostgreSQL/Redis startup failed."
}
else {
    Pass "PostgreSQL and Redis started."
}

Start-Sleep -Seconds 8

# ============================================================
# 6. MIGRATIONS
# ============================================================

Section "[6] DATABASE MIGRATIONS"
$MigrationOutput = Invoke-DockerComposeSafe @("run","--rm","--no-deps","aurix-api","alembic","upgrade","head")
foreach ($Line in $MigrationOutput) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -ne 0) {
    Fail "Alembic upgrade head failed."
}
else {
    Pass "Database migrations applied successfully."
}

$Heads = @(alembic heads 2>&1)

foreach ($Line in $Heads) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -eq 0) {

    $HeadLine = $Heads |
        Where-Object {
            $_ -match '^\w+.*\(head\)'
        } |
        Select-Object -Last 1

    if ($HeadLine) {
        Add-Report "LOCAL_ALEMBIC_HEAD=$HeadLine"
        Pass "Alembic migration head is discoverable."
    }
    else {
        Warn "Alembic head could not be parsed."
    }

}
else {
    Warn "Local Alembic heads command failed."
}

# ============================================================
# 7. START FULL APPLICATION
# ============================================================

Section "[7] FULL APPLICATION DEPLOYMENT"
$UpOutput = Invoke-DockerComposeSafe @("up","-d","--force-recreate","aurix-api","aurix-worker","aurix-client")
foreach ($Line in $UpOutput) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -ne 0) {
    Fail "Full application startup failed."
}
else {
    Pass "API, worker and frontend deployment started."
}

Start-Sleep -Seconds 20

# ============================================================
# 8. CONTAINER INVENTORY
# ============================================================

Section "[8] LIVE CONTAINER INVENTORY"
$ComposePs = Invoke-DockerComposeSafe @("ps")
foreach ($Line in $ComposePs) {
    Add-Report ([string]$Line)
}

$RequiredContainers = @(
    "aurix_enterprise_postgres",
    "aurix_enterprise_redis",
    "aurix_enterprise_api",
    "aurix_enterprise_worker",
    "aurix_enterprise_client"
)

foreach ($Container in $RequiredContainers) {

    $Exists = docker ps `
        --filter "name=^$Container$" `
        --format "{{.Names}}" 2>$null

    if ($Exists -eq $Container) {
        Pass "$Container is running."
    }
    else {
        Fail "$Container is not running."
    }
}

# ============================================================
# 9. API HEALTH
# ============================================================

Section "[9] LIVE API HEALTH"

try {

    $Health = Invoke-RestMethod `
        -Uri "http://localhost:8000/api/v1/health" `
        -Method Get `
        -TimeoutSec 15

    Add-Report (
        ($Health | ConvertTo-Json -Depth 8)
    )

    $Data = $Health.data

    if ($Data.status -eq "UP") {
        Pass "API health reports UP."
    }
    else {
        Fail "API health did not report UP."
    }

    if ($Data.environment -eq "production") {
        Pass "Live API environment is production."
    }
    else {
        Fail "Live API environment is not production."
    }

    if ($Data.build_version -eq "16.0.0") {
        Pass "Live API build_version is 16.0.0."
    }
    else {
        Fail "Unexpected live API build_version: $($Data.build_version)"
    }

    if ($Data.schema_version -eq "1.0.0") {
        Pass "Live API schema_version is 1.0.0."
    }
    else {
        Warn "Live API schema_version differs from expected 1.0.0: $($Data.schema_version)"
    }

    if ($Data.release_commit -eq $GitSha) {
        Pass "Live API release_commit matches Git HEAD."
    }
    else {
        Fail "Live API release_commit does not match Git HEAD."
    }

}
catch {
    Fail "Live API health request failed: $($_.Exception.Message)"
}

# ============================================================
# 10. API DOCUMENTATION SECURITY
# ============================================================

Section "[10] API DOCUMENTATION SECURITY"

foreach ($Path in @(
    "/docs",
    "/redoc",
    "/openapi.json"
)) {

    try {

        $Response = Invoke-WebRequest `
            -Uri ("http://localhost:8000" + $Path) `
            -UseBasicParsing `
            -TimeoutSec 10 `
            -ErrorAction Stop

        Add-Report "$Path -> HTTP $([int]$Response.StatusCode)"

        if ([int]$Response.StatusCode -eq 404) {
            Pass "$Path correctly disabled."
        }
        else {
            Fail "$Path is unexpectedly reachable."
        }

    }
    catch {

        $Status = 0

        try {
            $Status = [int]$_.Exception.Response.StatusCode
        }
        catch {
        }

        Add-Report "$Path -> HTTP $Status"

        if ($Status -eq 404) {
            Pass "$Path correctly disabled."
        }
        else {
            Fail "$Path validation failed."
        }
    }
}

# ============================================================
# 11. DATABASE RUNTIME IDENTITY
# ============================================================

Section "[11] DATABASE RUNTIME IDENTITY"

$DbProbe = docker exec `
    aurix_enterprise_api `
    python `
    -c `
    "from aurix_core.database.engine import engine; from sqlalchemy import text; c=engine.connect(); r=c.execute(text('select current_user, current_database()')).first(); print('current_user=' + str(r[0])); print('current_database=' + str(r[1])); c.close()"

foreach ($Line in $DbProbe) {
    Add-Report ([string]$Line)
}

if ($DbProbe -match "current_user=aurix_runtime") {
    Pass "Live API database connection uses aurix_runtime."
}
else {
    Fail "Live API database connection does not use aurix_runtime."
}

if ($DbProbe -match "current_database=aurix_db") {
    Pass "Live API database is aurix_db."
}
else {
    Fail "Live API database is not aurix_db."
}

# ============================================================
# 12. ALEMBIC CURRENT INSIDE RUNTIME
# ============================================================

Section "[12] RUNTIME MIGRATION STATE"

$RuntimeMigration = Invoke-DockerExecSafe @("aurix_enterprise_api","alembic","current")

foreach ($Line in $RuntimeMigration) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -eq 0) {

    if ($RuntimeMigration -match "0023_phase33_onboarding_staging") {
        Pass "Runtime database is at migration head 0023_phase33_onboarding_staging."
    }
    else {
        Fail "Runtime database migration head does not match expected 0023_phase33_onboarding_staging."
    }

}
else {
    Fail "Runtime Alembic current failed."
}

# ============================================================
# 13. WORKER EXECUTION
# ============================================================

Section "[13] WORKER EXECUTION + CONTROL PLANE"

$WorkerInspect = Invoke-DockerExecSafe @("aurix_enterprise_worker","celery","-A","aurix_core.worker.celery_app","inspect","ping")

foreach ($Line in $WorkerInspect) {
    Add-Report ([string]$Line)
}

if ($LASTEXITCODE -eq 0 -and $WorkerInspect -match "pong") {
    Pass "Celery control-plane ping succeeded."
}
else {
    Fail "Celery control-plane ping failed."
}
$WorkerState = (Invoke-DockerInspectSafe @("aurix_enterprise_worker","--format","{{.State.Status}}"))

if ($WorkerState -eq "running") {
    Pass "Worker container is running."
}
else {
    Fail "Worker container state is $WorkerState."
}

# ============================================================
# 14. FRONTEND RUNTIME
# ============================================================

Section "[14] FRONTEND RUNTIME"

try {

    $Frontend = Invoke-WebRequest `
        -Uri "http://localhost:3000/" `
        -UseBasicParsing `
        -TimeoutSec 15

    Add-Report "FRONTEND_HTTP_STATUS=$([int]$Frontend.StatusCode)"
    Add-Report "FRONTEND_RESPONSE_BYTES=$($Frontend.RawContentLength)"

    if ([int]$Frontend.StatusCode -eq 200) {
        Pass "Frontend root responds HTTP 200."
    }
    else {
        Fail "Frontend root did not return HTTP 200."
    }

}
catch {
    Fail "Frontend HTTP request failed: $($_.Exception.Message)"
}

# ============================================================
# 15. UNAUTHENTICATED REJECTION
# ============================================================

Section "[15] UNAUTHENTICATED REQUEST REJECTION"

$ProtectedRoutes = @(
    "/api/v1/capabilities",
    "/api/v1/analytics/overview"
)

$ProtectedSuccess = 0

foreach ($Route in $ProtectedRoutes) {

    try {

        $Response = Invoke-WebRequest `
            -Uri ("http://localhost:8000" + $Route) `
            -UseBasicParsing `
            -TimeoutSec 10 `
            -ErrorAction Stop

        Add-Report "$Route -> HTTP $([int]$Response.StatusCode)"

        if ([int]$Response.StatusCode -ge 400) {
            Pass "Unauthenticated request rejected for $Route."
        }
        else {
            Fail "Protected route $Route is reachable without authentication."
            $ProtectedSuccess++
        }

    }
    catch {

        $Status = 0

        try {
            $Status = [int]$_.Exception.Response.StatusCode
        }
        catch {
        }

        Add-Report "$Route -> HTTP $Status"

        if ($Status -eq 401 -or $Status -eq 403) {
            Pass "Unauthenticated request correctly rejected for $Route."
        }
        elseif ($Status -eq 404) {
            Warn "$Route returned 404; authentication rejection could not be proven."
        }
        else {
            Fail "Unexpected unauthenticated response for ${Route}: HTTP $Status"
        }
    }
}

# ============================================================
# 16. AUTHENTICATION TEST DISCOVERY
# ============================================================

Section "[16] AUTHENTICATION TEST COVERAGE"

Run-TestGroup `
    -GroupName "Authentication / authorization" `
    -Patterns @(
        "*auth*.py",
        "*login*.py",
        "test_p0_tenant_rls.py",
        "test_phase31_client_experience.py"
    )

# ============================================================
# 17. TENANT ISOLATION
# ============================================================

Section "[17] TENANT ISOLATION"

Run-TestGroup `
    -GroupName "Tenant isolation / RLS" `
    -Patterns @(
        "test_p0_tenant_rls.py",
        "*tenant*.py",
        "*rls*.py"
    )

# ============================================================
# 18. FILE UPLOAD / INGESTION
# ============================================================

Section "[18] FILE UPLOAD + INGESTION"

Run-TestGroup `
    -GroupName "File upload / ingestion" `
    -Patterns @(
        "*upload*.py",
        "*ingestion*.py",
        "test_phase19_data_fabric.py",
        "test_phase19_integration_lifecycle.py",
        "*onboarding*.py"
    )

# ============================================================
# 19. CSV / XLSX / JSON CONTRACT COVERAGE
# ============================================================

Section "[19] CSV / XLSX / JSON INGESTION COVERAGE"

$SourceFiles = @(
    Get-ChildItem `
        -LiteralPath $Root `
        -Recurse `
        -File `
        -Filter "*.py" `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch "\\\.venv\\" -and
            $_.FullName -notmatch "\\site-packages\\"
        }
)

$SourceText = ($SourceFiles | ForEach-Object {
    try {
        Get-Content -LiteralPath $_.FullName -Raw -ErrorAction Stop
    }
    catch {
        ""
    }
}) -join "`n"

foreach ($Format in @("csv", "xlsx", "json")) {

    if ($SourceText -match "(?i)\b$Format\b") {
        Pass "$Format ingestion implementation references discovered in source."
    }
    else {
        Fail "$Format ingestion implementation could not be discovered."
    }
}

$FormatTestFiles = Get-ExistingTestFiles -Patterns @(
    "*data*.py",
    "*ingestion*.py",
    "*onboarding*.py"
)

if ($FormatTestFiles.Count -gt 0) {

    foreach ($Format in @("CSV", "XLSX", "JSON")) {

        $Pattern = "(?i)$Format|$($Format.ToLower())"

        $Found = $false

        foreach ($File in $FormatTestFiles) {

            try {
                $Text = Get-Content -LiteralPath $File -Raw

                if ($Text -match $Pattern) {
                    $Found = $true
                    break
                }
            }
            catch {
            }
        }

        if ($Found) {
            Pass "$Format appears in ingestion/onboarding test coverage."
        }
        else {
            Not-Proven "$Format test coverage was not explicitly discovered."
        }
    }

}
else {
    Not-Proven "No ingestion/onboarding tests were discovered."
}

# ============================================================
# 20. SCHEMA DISCOVERY + QUALITY
# ============================================================

Section "[20] SCHEMA DISCOVERY + QUALITY/READINESS"

Run-TestGroup `
    -GroupName "Schema discovery / quality / readiness" `
    -Patterns @(
        "*schema*.py",
        "*quality*.py",
        "*readiness*.py",
        "*onboarding*.py",
        "test_phase19_data_fabric.py"
    )

# ============================================================
# 21. DOMAIN ANALYTICS
# ============================================================

Section "[21] DOMAIN ANALYTICS"

Run-TestGroup `
    -GroupName "Domain analytics" `
    -Patterns @(
        "*analytics*.py",
        "test_phase21_finance.py",
        "test_phase22_commercial.py",
        "test_phase23_manufacturing.py",
        "test_phase25_process_intelligence.py",
        "test_phase26_risk_intelligence.py"
    )

# ============================================================
# 22. DETERMINISTIC INTELLIGENCE
# ============================================================

Section "[22] DETERMINISTIC INTELLIGENCE"

Run-TestGroup `
    -GroupName "Deterministic intelligence" `
    -Patterns @(
        "test_deterministic_query_executor.py",
        "*deterministic*.py",
        "*intelligence*.py",
        "test_prephase32_canonical_bypass_audit.py",
        "test_prephase32_claim_answer_canonicalization.py",
        "test_prephase32_intelligence_boundary.py",
        "test_prephase32_orchestration_context.py"
    )

# ============================================================
# 23. GOVERNED AI
# ============================================================

Section "[23] GOVERNED AI PATH"

Run-TestGroup `
    -GroupName "Governed AI / agent path" `
    -Patterns @(
        "test_phase29_governed_agents.py",
        "test_phase30_agent_studio.py",
        "*agent*.py",
        "*ai*.py",
        "*intelligence*.py"
    )

# ============================================================
# 24. DECISION ENGINE
# ============================================================

Section "[24] DECISION ENGINE"

Run-TestGroup `
    -GroupName "Decision engine" `
    -Patterns @(
        "test_phase27_decision_engine.py",
        "*decision*.py"
    )

# ============================================================
# 25. SCENARIO ENGINE
# ============================================================

Section "[25] SCENARIO ENGINE"

Run-TestGroup `
    -GroupName "Scenario simulation" `
    -Patterns @(
        "test_phase28_scenario_simulation.py",
        "*scenario*.py"
    )

# ============================================================
# 26. ACTION GOVERNANCE
# ============================================================

Section "[26] ACTION GOVERNANCE"

Run-TestGroup `
    -GroupName "Controlled action governance" `
    -Patterns @(
        "test_phase14_actions.py",
        "*action*.py",
        "*governance*.py"
    )

# ============================================================
# 27. FRONTEND API CONTRACT
# ============================================================

Section "[27] FRONTEND API CONTRACT"

Run-TestGroup `
    -GroupName "Frontend/API contract" `
    -Patterns @(
        "test_frontend_contracts_and_search.py",
        "test_browser_e2e_smoke.py",
        "test_accessibility_and_performance.py",
        "test_phase31_client_experience.py"
    )

# ============================================================
# 28. FRONTEND PRODUCTION BUILD
# ============================================================

Section "[28] FRONTEND PRODUCTION BUILD"

$ClientPath = Join-Path $Root "aurix_client"

if (Test-Path -LiteralPath $ClientPath) {

    $PackageJson = Join-Path $ClientPath "package.json"

    if (Test-Path -LiteralPath $PackageJson) {

        Push-Location $ClientPath

        try {

            $BuildOutput = npm run build 2>&1

            foreach ($Line in $BuildOutput) {
                Add-Report ([string]$Line)
            }

            if ($LASTEXITCODE -eq 0) {
                Pass "Frontend production build succeeded."
            }
            else {
                Fail "Frontend production build failed."
            }

        }
        catch {
            Fail "Frontend production build failed: $($_.Exception.Message)"
        }
        finally {
            Pop-Location
        }

    }
    else {
        Fail "aurix_client/package.json not found."
    }

}
else {
    Fail "aurix_client directory not found."
}

# ============================================================
# 29. DOCKER IMAGE IDENTITY
# ============================================================

Section "[29] DOCKER IMAGE IDENTITY"

$Services = @(
    @{
        Container = "aurix_enterprise_api"
        Image = "aurix_engine-aurix-api:latest"
    },
    @{
        Container = "aurix_enterprise_worker"
        Image = "aurix_engine-aurix-worker:latest"
    },
    @{
        Container = "aurix_enterprise_client"
        Image = "aurix_engine-aurix-client:latest"
    }
)

foreach ($Item in $Services) {

    $ContainerDigest = docker inspect `
        $Item.Container `
        --format "{{.Image}}" 2>$null

    $ImageDigest = docker image inspect `
        $Item.Image `
        --format "{{.Id}}" 2>$null

    Add-Report "$($Item.Container) runtime image = $ContainerDigest"
    Add-Report "$($Item.Image) local image     = $ImageDigest"

    if (
        -not [string]::IsNullOrWhiteSpace($ContainerDigest) -and
        -not [string]::IsNullOrWhiteSpace($ImageDigest) -and
        $ContainerDigest -eq $ImageDigest
    ) {
        Pass "$($Item.Container) is running the current local image."
    }
    else {
        Fail "$($Item.Container) image identity does not match the current local image."
    }
}

# ============================================================
# 30. COMPLETE TEST COLLECTION
# ============================================================

Section "[30] FINAL TARGETED REGRESSION SUITE"

$CoreSuites = @(
    "tests/test_p0_tenant_rls.py",
    "tests/test_phase14_actions.py",
    "tests/test_phase16_step3.py",
    "tests/test_phase19_data_fabric.py",
    "tests/test_phase19_integration_lifecycle.py",
    "tests/test_phase20_assurance.py",
    "tests/test_phase21_finance.py",
    "tests/test_phase22_commercial.py",
    "tests/test_phase23_manufacturing.py",
    "tests/test_phase24_context_graph.py",
    "tests/test_phase25_process_intelligence.py",
    "tests/test_phase26_risk_intelligence.py",
    "tests/test_phase27_decision_engine.py",
    "tests/test_phase28_scenario_simulation.py",
    "tests/test_phase29_governed_agents.py",
    "tests/test_phase30_agent_studio.py",
    "tests/test_phase31_client_experience.py",
    "tests/test_deterministic_query_executor.py",
    "tests/test_frontend_contracts_and_search.py",
    "tests/test_docker_and_runtime_health.py"
)

$ExistingCoreSuites = @(
    foreach ($Suite in $CoreSuites) {
        $FullPath = Join-Path $Root $Suite

        if (Test-Path -LiteralPath $FullPath) {
            $FullPath
        }
    }
)

if ($ExistingCoreSuites.Count -eq 0) {

    Fail "No targeted regression suites were found."

}
else {

    Add-Report "TARGETED SUITES FOUND: $($ExistingCoreSuites.Count)"

    foreach ($Suite in $ExistingCoreSuites) {

        Add-Report ""
        Add-Report "RUNNING: $Suite"

        $TestResult = & $Python `
            -m pytest `
            -q `
            $Suite 2>&1

        foreach ($Line in $TestResult) {
            Add-Report ([string]$Line)
        }

        if ($LASTEXITCODE -ne 0) {
            Fail "Regression suite failed: $Suite"
        }
        else {
            Pass "Regression suite passed: $Suite"
        }
    }
}

# ============================================================
# 31. FINAL DOCKER STATE
# ============================================================

Section "[31] FINAL DOCKER STATE"

$FinalPs = docker ps `
    --format "table {{.Names}}`t{{.Status}}" 2>&1

foreach ($Line in $FinalPs) {
    Add-Report ([string]$Line)
}

foreach ($Container in $RequiredContainers) {

    $Status = docker inspect `
        $Container `
        --format "{{.State.Status}}" 2>$null

    if ($Status -eq "running") {
        Pass "Final runtime state: $Container = running."
    }
    else {
        Fail "Final runtime state: $Container = $Status."
    }
}

# ============================================================
# 32. FINAL HEALTH RECHECK
# ============================================================

Section "[32] FINAL HTTP RECHECK"

try {

    $FinalHealth = Invoke-RestMethod `
        -Uri "http://localhost:8000/api/v1/health" `
        -Method Get `
        -TimeoutSec 15

    if ($FinalHealth.data.status -eq "UP") {
        Pass "Final API health check reports UP."
    }
    else {
        Fail "Final API health check did not report UP."
    }

    if ($FinalHealth.data.release_commit -eq $GitSha) {
        Pass "Final API release identity matches Git HEAD."
    }
    else {
        Fail "Final API release identity mismatch."
    }

}
catch {
    Fail "Final HTTP health recheck failed: $($_.Exception.Message)"
}

try {

    $FinalFrontend = Invoke-WebRequest `
        -Uri "http://localhost:3000/" `
        -UseBasicParsing `
        -TimeoutSec 15

    if ([int]$FinalFrontend.StatusCode -eq 200) {
        Pass "Final frontend HTTP check reports 200."
    }
    else {
        Fail "Final frontend HTTP check returned HTTP $([int]$FinalFrontend.StatusCode)."
    }

}
catch {
    Fail "Final frontend HTTP check failed: $($_.Exception.Message)"
}

# ============================================================
# 33. REPORT
# ============================================================

Section "[33] STEP 12 FINAL GATE"

$PassCount = $Passes.Count
$WarningCount = $Warnings.Count
$FailCount = $Failures.Count

Add-Report ""
Add-Report "PASS COUNT       : $PassCount"
Add-Report "WARNING COUNT    : $WarningCount"
Add-Report "FAIL COUNT       : $FailCount"

if ($Failures.Count -eq 0) {

    Add-Report ""
    Add-Report "============================================================"
    Add-Report "AURIX API INTEGRATION READINESS"
    Add-Report "STATUS = READY"
    Add-Report "============================================================"

    Add-Report ""
    Add-Report "All mandatory Step 12 runtime gates passed."

    $FinalStatus = "READY"

}
else {

    Add-Report ""
    Add-Report "============================================================"
    Add-Report "AURIX API INTEGRATION READINESS"
    Add-Report "STATUS = NOT_READY"
    Add-Report "============================================================"

    Add-Report ""
    Add-Report "Outstanding failures:"

    foreach ($Failure in $Failures) {
        Add-Report "[FAIL] $Failure"
    }

    $FinalStatus = "NOT_READY"
}

Add-Report ""
Add-Report "Git SHA       : $GitSha"

try {
    $FinalTag = (git describe --tags --exact-match HEAD 2>$null).Trim()
}
catch {
    $FinalTag = ""
}

Add-Report "Git Tag       : $FinalTag"

Add-Report "Final Status  : $FinalStatus"
Add-Report "Report        : $ReportPath"

[System.IO.File]::WriteAllLines(
    $ReportPath,
    $ReportLines,
    [System.Text.UTF8Encoding]::new($false)
)

[System.IO.File]::WriteAllLines(
    $LatestPath,
    $ReportLines,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host ""
Write-Host "============================================================"
Write-Host "AURIX STEP 12 MASTER COMPLETE"
Write-Host "============================================================"
Write-Host "REPORT : $ReportPath"
Write-Host "STATUS : $FinalStatus"
Write-Host "PASS   : $PassCount"
Write-Host "WARN   : $WarningCount"
Write-Host "FAIL   : $FailCount"

if ($FinalStatus -ne "READY") {
    exit 1
}

exit 0
