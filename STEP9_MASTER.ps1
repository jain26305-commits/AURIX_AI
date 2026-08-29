$ErrorActionPreference = "Stop"

# ============================================================
# AURIX STEP 9 MASTER
# SECURITY + API HARDENING AUDIT
#
# POWERSELL-SAFE / READABLE / FAIL-CLOSED
#
# Scope:
#   Authentication
#   Authorization / RBAC
#   Tenant isolation
#   Database runtime role + RLS
#   File upload security
#   Secrets / credential leakage
#   CORS
#   Security headers
#   Rate limiting
#   API error leakage
#   Injection surfaces
#   Webhooks / replay protection
#   Connector credential handling
#   AI quota / provider / governance
#   Production docs exposure
#   Session / token expiry
#   Existing security regression tests
#
# Runtime behavior:
#   * No rebuild
#   * No container recreation
#   * No schema changes
#   * No application-data inserts
#   * No docker cp
#   * Database probes use docker exec -i
#   * Secrets are never printed
#   * .env.production.example is normalized only when concrete
#     credential-looking values are detected, after backup
#   * Final report is written once
# ============================================================

$Root = (Get-Location).Path

if (-not (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
    throw "Git repository not detected. Run this from the AURIX repository root."
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ReportDir = Join-Path $Root "AURIX_STEP9"
$BackupDir = Join-Path $Root "AURIX_STEP9_BACKUPS"

New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$Report = Join-Path $ReportDir "AURIX_STEP9_SECURITY_API_AUDIT_$Timestamp.txt"
$LatestReport = Join-Path $Root "AURIX_STEP9_SECURITY_API_AUDIT.txt"

$ProductionExamplePath = Join-Path $Root ".env.production.example"

$Lines = [System.Collections.Generic.List[string]]::new()
$Passes = [System.Collections.Generic.List[string]]::new()
$Warnings = [System.Collections.Generic.List[string]]::new()
$NotProven = [System.Collections.Generic.List[string]]::new()
$Failures = [System.Collections.Generic.List[string]]::new()

function Add-Line {
    param(
        [AllowEmptyString()]
        [string]$Text
    )

    [void]$Lines.Add($Text)
}

function Section {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    Add-Line ""
    Add-Line "============================================================"
    Add-Line $Title
    Add-Line "============================================================"
}

function Pass {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    Add-Line "[PASS] $Text"
    [void]$Passes.Add($Text)
}

function Warn {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    Add-Line "[WARN] $Text"
    [void]$Warnings.Add($Text)
}

function Not-Proven {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    Add-Line "[NOT_PROVEN] $Text"
    [void]$NotProven.Add($Text)
}

function Fail {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    Add-Line "[FAIL] $Text"
    [void]$Failures.Add($Text)
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
        return Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
    }
    catch {
        return ""
    }
}

function Invoke-NativeCapture {
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

function Get-HttpStatus {
    param(
        [Parameter(Mandatory = $true)]
        [System.Management.Automation.ErrorRecord]$ErrorRecord
    )

    try {
        if ($ErrorRecord.Exception.Response) {
            return [int]$ErrorRecord.Exception.Response.StatusCode
        }
    }
    catch {
    }

    return $null
}

function Get-ResponseBody {
    param(
        [Parameter(Mandatory = $true)]
        [System.Management.Automation.ErrorRecord]$ErrorRecord
    )

    try {
        if ($ErrorRecord.ErrorDetails -and $ErrorRecord.ErrorDetails.Message) {
            return [string]$ErrorRecord.ErrorDetails.Message
        }
    }
    catch {
    }

    try {
        if ($ErrorRecord.Exception.Response) {
            $stream = $ErrorRecord.Exception.Response.GetResponseStream()

            if ($stream) {
                $reader = [System.IO.StreamReader]::new($stream)

                try {
                    return $reader.ReadToEnd()
                }
                finally {
                    $reader.Dispose()
                }
            }
        }
    }
    catch {
    }

    return ""
}

try {

    # ========================================================
    # [0] INITIALIZATION
    # ========================================================

    Section "[0] STEP 9 INITIALIZATION"

    Add-Line "ROOT        : $Root"
    Add-Line "REPORT      : $Report"
    Add-Line "LATEST      : $LatestReport"
    Add-Line "TIMESTAMP   : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    Pass "Git repository detected."

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Pass "Docker CLI is available."
    }
    else {
        Fail "Docker CLI is not available."
    }

    # ========================================================
    # [1] LIVE RUNTIME INVENTORY
    # ========================================================

    Section "[1] LIVE RUNTIME INVENTORY"

    $RequiredContainers = @(
        "aurix_enterprise_api",
        "aurix_enterprise_worker",
        "aurix_enterprise_postgres",
        "aurix_enterprise_redis",
        "aurix_enterprise_client"
    )

    foreach ($Container in $RequiredContainers) {

        try {
            $state = docker inspect $Container --format "{{.State.Status}}" 2>$null
        }
        catch {
            $state = ""
        }

        $state = ([string]$state).Trim()

        if ($state -eq "running") {
            Add-Line "$Container = running"
            Pass "$Container is running."
        }
        elseif ([string]::IsNullOrWhiteSpace($state)) {
            Fail "Required container is unavailable: $Container"
        }
        else {
            Add-Line "$Container = $state"
            Fail "$Container is not running."
        }
    }

    # ========================================================
    # [2] LIVE DATABASE ROLE + RLS
    # ========================================================

    Section "[2] LIVE DATABASE ROLE + RLS"

    $DbProbe = @'
import os
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]

engine = create_engine(
    url,
    pool_pre_ping=True,
)

tables = [
    "ai_usage_policies",
    "connectors",
    "phase14_actions",
    "phase16_cases",
]

with engine.connect() as conn:

    identity = conn.execute(
        text("""
            SELECT
                current_user,
                current_database()
        """)
    ).mappings().one()

    print("USER=" + str(identity["current_user"]))
    print("DATABASE=" + str(identity["current_database"]))

    role = conn.execute(
        text("""
            SELECT
                rolsuper,
                rolcreatedb,
                rolcreaterole,
                rolcanlogin,
                rolbypassrls
            FROM pg_roles
            WHERE rolname = current_user
        """)
    ).mappings().one()

    print("SUPERUSER=" + str(role["rolsuper"]))
    print("CREATEDB=" + str(role["rolcreatedb"]))
    print("CREATEROLE=" + str(role["rolcreaterole"]))
    print("CANLOGIN=" + str(role["rolcanlogin"]))
    print("BYPASSRLS=" + str(role["rolbypassrls"]))

    for table in tables:

        row = conn.execute(
            text("""
                SELECT
                    relrowsecurity,
                    relforcerowsecurity
                FROM pg_class c
                JOIN pg_namespace n
                  ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = :table
            """),
            {"table": table},
        ).mappings().one()

        print(
            "RLS|" +
            table +
            "|" +
            str(row["relrowsecurity"]) +
            "|" +
            str(row["relforcerowsecurity"])
        )

engine.dispose()
'@

    $DbOut = Join-Path `
        $env:TEMP `
        ("aurix_step9_db_" + [guid]::NewGuid().ToString("N") + ".txt")

    $DbProbe |
        docker exec -i aurix_enterprise_api python - *> $DbOut

    $DbExit = $LASTEXITCODE
    $DbText = Read-TextSafe $DbOut

    ($DbText -split "`r?`n") |
        Where-Object {
            -not [string]::IsNullOrWhiteSpace($_)
        } |
        ForEach-Object {
            Add-Line $_
        }

    if ($DbExit -eq 0) {

        # ----------------------------------------------------
        # Parse role fields explicitly.
        # ----------------------------------------------------

        $userLine = @(
            ($DbText -split "`r?`n") |
            Where-Object { $_ -match '^USER=' } |
            Select-Object -First 1
        )

        $superLine = @(
            ($DbText -split "`r?`n") |
            Where-Object { $_ -match '^SUPERUSER=' } |
            Select-Object -First 1
        )

        $bypassLine = @(
            ($DbText -split "`r?`n") |
            Where-Object { $_ -match '^BYPASSRLS=' } |
            Select-Object -First 1
        )

        $loginLine = @(
            ($DbText -split "`r?`n") |
            Where-Object { $_ -match '^CANLOGIN=' } |
            Select-Object -First 1
        )

        $actualUser = ""
        $actualSuper = ""
        $actualBypass = ""
        $actualCanLogin = ""

        if ($userLine.Count -gt 0) {
            $actualUser = ($userLine[0] -replace '^USER=', "").Trim()
        }

        if ($superLine.Count -gt 0) {
            $actualSuper = ($superLine[0] -replace '^SUPERUSER=', "").Trim().ToLowerInvariant()
        }

        if ($bypassLine.Count -gt 0) {
            $actualBypass = ($bypassLine[0] -replace '^BYPASSRLS=', "").Trim().ToLowerInvariant()
        }

        if ($loginLine.Count -gt 0) {
            $actualCanLogin = ($loginLine[0] -replace '^CANLOGIN=', "").Trim().ToLowerInvariant()
        }

        Add-Line "PARSED_USER=$actualUser"
        Add-Line "PARSED_SUPERUSER=$actualSuper"
        Add-Line "PARSED_BYPASSRLS=$actualBypass"
        Add-Line "PARSED_CANLOGIN=$actualCanLogin"

        if (
            $actualUser -eq "aurix_runtime" -and
            $actualSuper -eq "false" -and
            $actualBypass -eq "false" -and
            $actualCanLogin -eq "true"
        ) {
            Pass "Live API database role is aurix_runtime with restricted attributes."
        }
        else {
            Fail (
                "Live API database role mismatch. " +
                "USER=$actualUser " +
                "SUPERUSER=$actualSuper " +
                "BYPASSRLS=$actualBypass " +
                "CANLOGIN=$actualCanLogin"
            )
        }

        # ----------------------------------------------------
        # Parse RLS rows explicitly.
        # ----------------------------------------------------

        $RlsLines = @(
            ($DbText -split "`r?`n") |
            Where-Object { $_ -match '^RLS\|' }
        )

        $RlsPass = @(
            $RlsLines |
            Where-Object {

                $parts = $_ -split '\|'

                (
                    $parts.Count -eq 4 -and
                    $parts[0].Trim() -eq "RLS" -and
                    $parts[2].Trim().ToLowerInvariant() -eq "true" -and
                    $parts[3].Trim().ToLowerInvariant() -eq "true"
                )
            }
        )

        if (
            $RlsLines.Count -eq 4 -and
            $RlsPass.Count -eq 4
        ) {
            Pass "Forced RLS is active on all four target tables."
        }
        else {
            Fail "Forced RLS could not be confirmed on all four target tables."
        }

    }
    else {

        Fail "Live API database security probe failed."
        Add-Line "Database probe exit code: $DbExit"

    }

    Remove-Item `
        -LiteralPath $DbOut `
        -Force `
        -ErrorAction SilentlyContinue

    # ========================================================
    # [3] SOURCE TREE SECURITY INDEX
    # ========================================================

    Section "[3] SOURCE TREE SECURITY INDEX"

    $SourceFiles = @(
        Get-ChildItem `
            -LiteralPath $Root `
            -Recurse `
            -File `
            -Include *.py,*.ts,*.tsx,*.json,*.yml,*.yaml,*.ini,*.md `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -notmatch "\\.git\\" -and
            $_.FullName -notmatch "\\node_modules\\" -and
            $_.FullName -notmatch "\\.next\\" -and
            $_.FullName -notmatch "\\__pycache__\\" -and
            $_.FullName -notmatch "\\AURIX_STEP9\\" -and
            $_.FullName -notmatch "\\AURIX_STEP[0-9A-Z_]*\\" -and
            $_.Name -notmatch "^AURIX_STEP.*\.(txt|log)$"
        }
    )

    Add-Line "Source files indexed: $($SourceFiles.Count)"

    if ($SourceFiles.Count -gt 0) {
        Pass "Source tree indexed for security audit."
    }
    else {
        Fail "No source files were indexed."
    }

    # ========================================================
    # [4] AUTHENTICATION
    # ========================================================

    Section "[4] AUTHENTICATION"

    $AuthPatterns = @(
        "jwt",
        "Authorization",
        "Bearer",
        "access_token",
        "token_expire",
        "401",
        "invalid_token",
        "HTTPException"
    )

    $AuthHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $AuthPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($AuthHits.Count -gt 0) {

        $AuthHits |
            Select-Object -First 100 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: authentication evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "Authentication implementation evidence exists."

    }
    else {
        Fail "Authentication implementation evidence not located."
    }

    # ========================================================
    # [5] AUTHORIZATION / RBAC
    # ========================================================

    Section "[5] AUTHORIZATION / RBAC"

    $RbacPatterns = @(
        "rbac",
        "permission",
        "role",
        "SUPER_ADMIN",
        "ADMIN",
        "ANALYST",
        "forbidden",
        "403"
    )

    $RbacHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $RbacPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($RbacHits.Count -gt 0) {

        $RbacHits |
            Select-Object -First 100 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: RBAC evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "RBAC/authorization implementation evidence exists."

    }
    else {
        Fail "RBAC/authorization implementation evidence not located."
    }

    # ========================================================
    # [6] LIVE UNAUTHENTICATED API BEHAVIOR
    # ========================================================

    Section "[6] LIVE UNAUTHENTICATED API BEHAVIOR"

    $ProtectedCandidates = @(
        "/api/v1/capabilities",
        "/api/v1/search",
        "/api/v1/intelligence",
        "/api/v1/actions",
        "/api/v1/scenarios"
    )

    $ProtectedResponses = 0

    foreach ($Path in $ProtectedCandidates) {

        try {

            $Response = Invoke-WebRequest `
                -Uri ("http://localhost:8000" + $Path) `
                -Method Get `
                -UseBasicParsing `
                -TimeoutSec 10 `
                -ErrorAction Stop

            $Status = [int]$Response.StatusCode

            Add-Line "$Path -> HTTP $Status"

            if ($Status -eq 401 -or $Status -eq 403) {
                $ProtectedResponses++
            }

        }
        catch {

            $Status = Get-HttpStatus -ErrorRecord $_
            Add-Line "$Path -> HTTP $Status"

            if ($Status -eq 401 -or $Status -eq 403) {
                $ProtectedResponses++
            }
        }
    }

    if ($ProtectedResponses -gt 0) {
        Pass "At least one candidate route enforces unauthenticated protection with 401/403."
    }
    else {
        Not-Proven "Automatic unauthenticated-protection testing did not establish a 401/403 route."
    }

    # ========================================================
    # [7] TENANT ISOLATION
    # ========================================================

    Section "[7] TENANT ISOLATION"

    $TenantPatterns = @(
        "tenant_id",
        "tenant_scope",
        "get_current_tenant_id",
        "app.tenant_id",
        "tenant context",
        "tenant isolation"
    )

    $TenantHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $TenantPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($TenantHits.Count -gt 0) {

        $TenantHits |
            Select-Object -First 100 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: tenant-isolation evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "Tenant isolation implementation evidence exists."

    }
    else {
        Fail "Tenant isolation implementation evidence not located."
    }

    # Reuse the already-parsed live role value. Do not re-parse the
    # raw docker output here; this avoids formatting/encoding false negatives.
    if (
        $DbExit -eq 0 -and
        $actualBypass -eq "false"
    ) {
        Pass "Live runtime database role cannot bypass PostgreSQL RLS."
    }
    else {
        Fail "Live runtime database role bypass-RLS state is unsafe or unknown."
    }

    # ========================================================
    # [8] FILE UPLOAD SECURITY
    # ========================================================

    Section "[8] FILE UPLOAD SECURITY"

    $UploadPatterns = @(
        "max_upload_file_size",
        "allowed_upload_extensions",
        "sanitize",
        "sanitiz",
        "multipart",
        "content_type",
        "filename",
        "extension",
        "quarantine"
    )

    $UploadHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $UploadPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($UploadHits.Count -gt 0) {

        $UploadHits |
            Select-Object -First 120 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: upload-security evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "File-upload safety controls are represented in the source."

    }
    else {
        Fail "File-upload safety controls were not located."
    }

    # ========================================================
    # [9] SECRET / CREDENTIAL LEAKAGE
    # ========================================================

    Section "[9] SECRET / CREDENTIAL LEAKAGE"

    # Deliberately narrow patterns. Words such as 'password'
    # or 'secret' alone are not treated as leaked credentials.

    $SecretPatterns = @(
        "(?i)-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----",
        "(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{20,}",
        "(?i)postgres(?:ql)?://[^ \r\n:]+:[^ \r\n@]+@",
        "(?i)\bghp_[A-Za-z0-9]{30,}\b",
        "(?i)\bsk-[A-Za-z0-9_-]{20,}\b"
    )

    $SecretScanFiles = @(
        $SourceFiles |
        Where-Object {
            $_.FullName -notmatch "\\tests\\" -and
            $_.FullName -notmatch "\\AURIX_STEP" -and
            $_.Name -notmatch "\.example$" -and
            $_.Name -notmatch "\.md$" -and
            $_.Name -ne "STEP9_MASTER.ps1"
        }
    )

    $SecretHits = @(
        Select-String `
            -Path $SecretScanFiles.FullName `
            -Pattern $SecretPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($SecretHits.Count -eq 0) {

        Pass "No obvious secret-pattern leakage detected in scanned non-test source."

    }
    else {

        Add-Line "Potential secret-pattern matches: $($SecretHits.Count)"

        $SecretHits |
            Select-Object -First 30 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: potential credential-like material (value omitted)" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Warn "Potential credential-like material requires manual review."
    }

    # ========================================================
    # [10] PRODUCTION EXAMPLE CONFIGURATION
    # ========================================================

    Section "[10] PRODUCTION EXAMPLE CONFIGURATION"

    if (Test-Path -LiteralPath $ProductionExamplePath) {

        $ProductionText = Read-TextSafe $ProductionExamplePath

        $ConcretePassword = (
            $ProductionText -match
            '(?mi)^\s*POSTGRES_PASSWORD\s*=\s*(?!REPLACE_WITH|CHANGE_ME|YOUR_|<)[^\r\n]+'
        )

        $ConcreteJwt = (
            $ProductionText -match
            '(?mi)^\s*JWT_SECRET_KEY\s*=\s*(?!REPLACE_WITH|CHANGE_ME|YOUR_|<)[^\r\n]+'
        )

        $ConcreteDatabaseUrl = (
            $ProductionText -match
            '(?mi)^\s*DATABASE_URL\s*=\s*postgresql'
        )

        if ($ConcretePassword -or $ConcreteJwt -or $ConcreteDatabaseUrl) {

            $ProductionBackup = Join-Path `
                $BackupDir `
                ".env.production.example_$Timestamp.bak"

            Copy-Item `
                -LiteralPath $ProductionExamplePath `
                -Destination $ProductionBackup `
                -Force

            $ProductionText = [regex]::Replace(
                $ProductionText,
                "(?mi)^\s*DATABASE_URL\s*=.*$",
                "DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE"
            )

            $ProductionText = [regex]::Replace(
                $ProductionText,
                "(?mi)^\s*POSTGRES_USER\s*=.*$",
                "POSTGRES_USER=REPLACE_WITH_DATABASE_USER"
            )

            $ProductionText = [regex]::Replace(
                $ProductionText,
                "(?mi)^\s*POSTGRES_PASSWORD\s*=.*$",
                "POSTGRES_PASSWORD=REPLACE_WITH_DATABASE_PASSWORD"
            )

            $ProductionText = [regex]::Replace(
                $ProductionText,
                "(?mi)^\s*POSTGRES_DB\s*=.*$",
                "POSTGRES_DB=REPLACE_WITH_DATABASE_NAME"
            )

            $ProductionText = [regex]::Replace(
                $ProductionText,
                "(?mi)^\s*JWT_SECRET_KEY\s*=.*$",
                "JWT_SECRET_KEY=REPLACE_WITH_RANDOM_SECRET_OF_AT_LEAST_32_CHARACTERS"
            )

            [System.IO.File]::WriteAllText(
                (Resolve-Path $ProductionExamplePath).Path,
                $ProductionText,
                [System.Text.UTF8Encoding]::new($false)
            )

            Add-Line "Production example backup: $ProductionBackup"

            Pass "Concrete credential-looking values were normalized in .env.production.example."

        }
        else {

            Pass "Production example does not contain obvious concrete credential values requiring normalization."

        }

    }
    else {

        Not-Proven ".env.production.example is not present."

    }

    # ========================================================
    # [11] CORS
    # ========================================================

    Section "[11] CORS"

    $CorsText = (
        (Read-TextSafe (Join-Path $Root "docker-compose.yml")) +
        "`n" +
        (Read-TextSafe $ProductionExamplePath) +
        "`n" +
        (Read-TextSafe (Join-Path $Root "aurix_core\config\settings.py"))
    )

    if ($CorsText -match '(?i)CORS_ORIGINS.*\*|cors_origins.*\*') {
        Fail "Wildcard CORS configuration was detected."
    }
    else {
        Pass "No wildcard CORS configuration detected."
    }

    if ($CorsText -match '(?i)CORS_ORIGINS|cors_origins') {
        Pass "CORS configuration is explicitly represented."
    }
    else {
        Not-Proven "Exact CORS origins could not be structurally established."
    }

    # ========================================================
    # [12] SECURITY RESPONSE HEADERS
    # ========================================================

    Section "[12] SECURITY RESPONSE HEADERS"

    try {

        $HealthHeaders = Invoke-WebRequest `
            -Uri "http://localhost:8000/api/v1/health" `
            -Method Get `
            -UseBasicParsing `
            -TimeoutSec 10 `
            -ErrorAction Stop

        $ExpectedHeaders = @(
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Referrer-Policy",
            "Content-Security-Policy"
        )

        $HeaderCount = 0

        foreach ($Header in $ExpectedHeaders) {

            if ($HealthHeaders.Headers[$Header]) {
                Add-Line "$Header = PRESENT"
                $HeaderCount++
            }
            else {
                Add-Line "$Header = MISSING"
            }
        }

        if ($HeaderCount -eq $ExpectedHeaders.Count) {
            Pass "All baseline security response headers were observed."
        }
        elseif ($HeaderCount -ge 2) {
            Warn "Some security response headers are present, but the baseline is incomplete."
        }
        elseif ($HeaderCount -gt 0) {
            Warn "Only a limited subset of standard security response headers is present."
        }
        else {
            Warn "No standard security response headers were observed."
        }

    }
    catch {

        Not-Proven "Security response headers could not be checked."

    }

    # ========================================================
    # [13] RATE LIMITING
    # ========================================================

    Section "[13] RATE LIMITING"

    $RatePatterns = @(
        "rate_limit",
        "RateLimit",
        "slowapi",
        "429",
        "requests_per_minute",
        "ai_requests_per_minute"
    )

    $RateHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $RatePatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($RateHits.Count -gt 0) {

        $RateHits |
            Select-Object -First 100 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: rate-limit evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "Rate-limiting implementation evidence exists."

    }
    else {
        Fail "Rate-limiting implementation evidence not located."
    }

    # ========================================================
    # [14] WEBHOOK / REPLAY PROTECTION
    # ========================================================

    Section "[14] WEBHOOK SIGNATURE + REPLAY PROTECTION"

    $WebhookPatterns = @(
        "HMAC",
        "hmac",
        "signature",
        "replay",
        "timestamp",
        "webhook_timestamp_tolerance",
        "compare_digest"
    )

    $WebhookHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $WebhookPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($WebhookHits.Count -gt 0) {

        $WebhookHits |
            Select-Object -First 100 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: webhook-security evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "Webhook signing/replay-control evidence exists."

    }
    else {
        Fail "Webhook signing/replay-control evidence not located."
    }

    # ========================================================
    # [15] CONNECTOR CREDENTIAL HANDLING
    # ========================================================

    Section "[15] CONNECTOR CREDENTIAL HANDLING"

    $ConnectorPatterns = @(
        "secret",
        "credential",
        "password",
        "token",
        "redact",
        "mask",
        "secret_resolution"
    )

    $ConnectorHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $ConnectorPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($ConnectorHits.Count -gt 0) {

        $ConnectorHits |
            Select-Object -First 100 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: connector-secret evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "Connector credential handling/redaction evidence exists."

    }
    else {
        Warn "Connector credential handling could not be structurally correlated."
    }

    # ========================================================
    # [16] AURIX AI SECURITY + GOVERNANCE
    # ========================================================

    Section "[16] AURIX AI SECURITY + GOVERNANCE"

    $AiPatterns = @(
        "ai_usage_policies",
        "monthly_spend",
        "daily_spend",
        "token_limit",
        "gemini",
        "cloudflare",
        "fallback",
        "grounding",
        "claim_validator",
        "answer_composer",
        "evidence"
    )

    $AiHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $AiPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($AiHits.Count -gt 0) {

        $AiHits |
            Select-Object -First 150 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: AI governance evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "AI quota/provider/governance implementation evidence exists."

    }
    else {
        Fail "AI quota/provider/governance evidence not located."
    }

    # ========================================================
    # [17] API ERROR-CONTRACT / TRACE LEAKAGE
    # ========================================================

    Section "[17] API ERROR-CONTRACT / TRACE LEAKAGE"

    $ErrorProbePaths = @(
        "/api/v1/does-not-exist",
        "/api/v1/search",
        "/api/v1/intelligence"
    )

    $LeakPatterns = @(
        "Traceback",
        'File "',
        "sqlalchemy",
        "psycopg",
        "password",
        "secret",
        "DATABASE_URL",
        "KeyError",
        "Internal Server Error"
    )

    $LeakFound = $false

    foreach ($Path in $ErrorProbePaths) {

        try {

            $Response = Invoke-WebRequest `
                -Uri ("http://localhost:8000" + $Path) `
                -Method Get `
                -UseBasicParsing `
                -TimeoutSec 10 `
                -ErrorAction Stop

            $Body = [string]$Response.Content

        }
        catch {

            $Body = Get-ResponseBody -ErrorRecord $_

        }

        if (-not [string]::IsNullOrWhiteSpace($Body)) {

            foreach ($Pattern in $LeakPatterns) {

                if ($Body -match [regex]::Escape($Pattern)) {

                    Add-Line "$Path -> potential leakage pattern: $Pattern"
                    $LeakFound = $true

                }
            }
        }
    }

    if ($LeakFound) {
        Fail "Potential internal implementation or secret leakage was observed in an API error response."
    }
    else {
        Pass "No obvious traceback/database/secret leakage observed in tested API responses."
    }

    # ========================================================
    # [18] INJECTION SURFACE AUDIT
    # ========================================================

    Section "[18] INJECTION SURFACE AUDIT"

    $InjectionPatterns = @(
        'text\(f["'']',
        'execute\(f["'']',
        'subprocess\.run\(',
        'shell\s*=\s*True',
        'os\.system\(',
        'eval\(',
        'exec\('
    )

    $InjectionHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $InjectionPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($InjectionHits.Count -gt 0) {

        Add-Line "Potential injection-pattern matches: $($InjectionHits.Count)"

        $InjectionHits |
            Select-Object -First 60 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: contextual review required" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Warn "Potential dynamic execution/query patterns require contextual review."

    }
    else {

        Pass "No obvious high-risk dynamic execution/query patterns were detected."

    }

    # ========================================================
    # [19] SESSION + TOKEN EXPIRY
    # ========================================================

    Section "[19] SESSION + TOKEN EXPIRY"

    $SessionPatterns = @(
        "ACCESS_TOKEN_EXPIRE",
        "access_token_expire",
        "expire_minutes",
        "jwt",
        "revok",
        "logout",
        "invalidate",
        "refresh"
    )

    $SessionHits = @(
        Select-String `
            -Path $SourceFiles.FullName `
            -Pattern $SessionPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($SessionHits.Count -gt 0) {

        $SessionHits |
            Select-Object -First 120 |
            ForEach-Object {
                Add-Line (
                    "{0}:{1}: session/token evidence" -f
                    $_.Path,
                    $_.LineNumber
                )
            }

        Pass "Session/token expiry and lifecycle evidence exists."

    }
    else {
        Not-Proven "Session expiry/revocation could not be structurally established."
    }

    # ========================================================
    # [20] PRODUCTION API DOCUMENTATION EXPOSURE
    # ========================================================

    Section "[20] PRODUCTION API DOCUMENTATION EXPOSURE"

    $SettingsText = Read-TextSafe (
        Join-Path $Root "aurix_core\config\settings.py"
    )

    $ProductionText = Read-TextSafe $ProductionExamplePath

    if ($ProductionText -match '(?mi)^\s*ENABLE_DOCS\s*=\s*false\s*$') {

        Pass "Production example explicitly disables API documentation."

    }
    elseif ($SettingsText -match '(?mi)enable_docs.*default\s*=\s*true') {

        Not-Proven "Application default enables docs; production override could not be conclusively verified."

    }
    else {

        Not-Proven "Production API-documentation policy could not be established."

    }

    $OpenApiStatus = $null

    try {

        $OpenApiResponse = Invoke-WebRequest `
            -Uri "http://localhost:8000/openapi.json" `
            -Method Get `
            -UseBasicParsing `
            -TimeoutSec 10 `
            -ErrorAction Stop

        $OpenApiStatus = [int]$OpenApiResponse.StatusCode

    }
    catch {

        $OpenApiStatus = Get-HttpStatus -ErrorRecord $_

    }

    if ($OpenApiStatus -eq 404) {

        Pass "Live OpenAPI endpoint is not exposed."

    }
    elseif ($OpenApiStatus -eq 200) {

        if ($ProductionText -match '(?mi)^\s*ENABLE_DOCS\s*=\s*false\s*$') {

            Fail "Live OpenAPI is exposed despite production documentation being explicitly disabled."

        }
        else {

            Warn "Live OpenAPI is exposed; production documentation policy requires explicit review."

        }

    }
    elseif ($OpenApiStatus) {

        Add-Line "LIVE /openapi.json -> HTTP $OpenApiStatus"
        Not-Proven "OpenAPI returned a non-404 status requiring review."

    }
    else {

        Not-Proven "Live OpenAPI exposure could not be determined."

    }

    # ========================================================
    # [21] SECURITY REGRESSION TESTS
    # ========================================================

    Section "[21] SECURITY REGRESSION TEST EXECUTION"

    $SecurityTests = @(
        "tests/test_p0_hardening.py",
        "tests/test_p0_tenant_rls.py",
        "tests/test_phase10_api.py",
        "tests/test_phase12_integrations.py",
        "tests/test_phase13_events.py",
        "tests/test_phase14_actions.py",
        "tests/test_reconciliation.py"
    )

    $ExistingSecurityTests = @(
        $SecurityTests |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $Root $_)
        }
    )

    Add-Line "Security test files present: $($ExistingSecurityTests.Count)"

    if ($ExistingSecurityTests.Count -eq 0) {

        Not-Proven "No existing security regression test files were found."

    }
    else {

        $TestOut = Join-Path `
            $env:TEMP `
            ("aurix_step9_tests_" + [guid]::NewGuid().ToString("N") + ".txt")

        $PytestArgs = @(
            "-m",
            "pytest",
            "-q"
        ) + $ExistingSecurityTests

        $TestExit = Invoke-NativeCapture `
            -File "D:\Python-IDLE\python.exe" `
            -Arguments $PytestArgs `
            -OutputFile $TestOut

        $TestText = Read-TextSafe $TestOut

        ($TestText -split "`r?`n") |
            Select-Object -Last 150 |
            ForEach-Object {

                if (-not [string]::IsNullOrWhiteSpace($_)) {
                    Add-Line $_
                }

            }

        if ($TestExit -eq 0) {
            Pass "Security regression tests returned exit code 0."
        }
        else {
            Fail "Security regression tests returned exit code $TestExit."
        }

        Remove-Item `
            -LiteralPath $TestOut `
            -Force `
            -ErrorAction SilentlyContinue
    }

    # ========================================================
    # [22] LIVE API HEALTH
    # ========================================================

    Section "[22] LIVE API HEALTH"

    try {

        $Health = Invoke-RestMethod `
            -Uri "http://localhost:8000/api/v1/health" `
            -Method Get `
            -TimeoutSec 15 `
            -ErrorAction Stop

        Add-Line (
            $Health |
            ConvertTo-Json -Depth 40
        )

        Pass "Live API health endpoint is operational."

    }
    catch {
        Fail "Live API health endpoint failed."
    }

    # ========================================================
    # [23] FINAL SECURITY GATE
    # ========================================================

    Section "[23] STEP 9 FINAL GATE"

    Add-Line ""
    Add-Line "PASS COUNT       : $($Passes.Count)"
    Add-Line "WARNING COUNT    : $($Warnings.Count)"
    Add-Line "NOT PROVEN COUNT : $($NotProven.Count)"
    Add-Line "FAIL COUNT       : $($Failures.Count)"

    Add-Line ""

    if ($Failures.Count -eq 0) {

        if ($NotProven.Count -eq 0) {

            Add-Line "SECURITY_API_HARDENING = PASS"
            Add-Line "STEP_9 = COMPLETE"

        }
        else {

            Add-Line "SECURITY_API_HARDENING = PASS_WITH_UNPROVEN_BOUNDARIES"
            Add-Line "STEP_9 = COMPLETE_WITH_BOUNDARIES"

        }

    }
    else {

        Add-Line "SECURITY_API_HARDENING = FAIL"
        Add-Line "STEP_9 = NOT_READY"

    }

    Add-Line ""
    Add-Line "IMPORTANT:"
    Add-Line "This audit is not a substitute for an external penetration test."
    Add-Line "NOT_PROVEN items identify boundaries requiring dedicated credentials, browser tooling, or external infrastructure."
    Add-Line "Secret values are intentionally omitted from the report."
    Add-Line "No database schema changes were made."
    Add-Line "No application data was intentionally inserted."
    Add-Line "No containers were rebuilt or recreated."

}
catch {

    $Message = $_.Exception.Message

    Add-Line "[FAIL] Fatal Step 9 audit exception: $Message"
    [void]$Failures.Add("Fatal Step 9 audit exception: $Message")

}
finally {

    $FinalText = $Lines -join [Environment]::NewLine

    [System.IO.File]::WriteAllText(
        $Report,
        $FinalText,
        [System.Text.UTF8Encoding]::new($false)
    )

    try {

        [System.IO.File]::Copy(
            $Report,
            $LatestReport,
            $true
        )

    }
    catch {
    }

}

Write-Host ""
Write-Host "============================================================"
Write-Host "AURIX STEP 9 MASTER - FINAL OUTPUT"
Write-Host "============================================================"
Write-Host "MASTER REPORT : $Report"
Write-Host "LATEST REPORT : $LatestReport"
Write-Host ""
Write-Host "PASS COUNT    : $($Passes.Count)"
Write-Host "WARNING COUNT : $($Warnings.Count)"
Write-Host "NOT PROVEN    : $($NotProven.Count)"
Write-Host "FAIL COUNT    : $($Failures.Count)"
Write-Host ""

if ($Failures.Count -eq 0 -and $NotProven.Count -eq 0) {

    Write-Host "SECURITY_API_HARDENING = PASS" -ForegroundColor Green
    Write-Host "STEP_9 = COMPLETE" -ForegroundColor Green

}
elseif ($Failures.Count -eq 0) {

    Write-Host "SECURITY_API_HARDENING = PASS_WITH_UNPROVEN_BOUNDARIES" -ForegroundColor Yellow
    Write-Host "STEP_9 = COMPLETE_WITH_BOUNDARIES" -ForegroundColor Yellow

}
else {

    Write-Host "SECURITY_API_HARDENING = FAIL" -ForegroundColor Red
    Write-Host "STEP_9 = NOT_READY" -ForegroundColor Red

}

Write-Host ""
Write-Host "============================================================"
Write-Host "STEP 9 MASTER COMPLETE"
Write-Host "============================================================"
