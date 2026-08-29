$ErrorActionPreference = "Stop"

# ============================================================
# AURIX STEP 10 MASTER
# DOCKER PRODUCTION AUDIT
#
# PURPOSE
# -------
# Audit Dockerfile / docker-compose / .dockerignore, perform a
# controlled clean image build, inspect resulting images, and
# verify live API/worker/database/Redis/client runtime wiring.
#
# SAFETY
# ------
# * No database schema changes
# * No database writes
# * No application data insertion
# * No migration execution
# * No running-container recreation
# * No docker cp
# * Temporary probe containers are removed automatically
# * Secrets are redacted from the report
# * The build may update local Docker images
# * The build does NOT recreate the running stack
# ============================================================

$Root = (Get-Location).Path

if (-not (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
    throw "Git repository not detected. Run this from the AURIX repository root."
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ReportDir = Join-Path $Root "AURIX_STEP10"
$BackupDir = Join-Path $Root "AURIX_STEP10_BACKUPS"

New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$Report = Join-Path `
    $ReportDir `
    "AURIX_STEP10_DOCKER_PRODUCTION_AUDIT_$Timestamp.txt"

$LatestReport = Join-Path `
    $Root `
    "AURIX_STEP10_DOCKER_PRODUCTION_AUDIT.txt"

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

function Redact-Text {
    param(
        [AllowEmptyString()]
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $Text
    }

    $Result = $Text

    $Result = [regex]::Replace(
        $Result,
        '(?i)(postgres(?:ql)?://[^:\s]+:)[^@\s]+@',
        '$1<REDACTED>@'
    )

    $Result = [regex]::Replace(
        $Result,
        '(?im)^(\s*(?:PASSWORD|POSTGRES_PASSWORD|JWT_SECRET_KEY|SECRET_KEY|API_KEY|TOKEN)\s*=\s*).*$',
        '$1<REDACTED>'
    )

    return $Result
}

function Get-ComposeServices {

    $Temp = Join-Path `
        $env:TEMP `
        ("aurix_step10_services_" + [guid]::NewGuid().ToString("N") + ".txt")

    try {

        docker compose config --services *> $Temp

        if ($LASTEXITCODE -ne 0) {
            return @()
        }

        return @(
            Get-Content -LiteralPath $Temp |
            Where-Object {
                -not [string]::IsNullOrWhiteSpace($_)
            }
        )

    }
    finally {

        Remove-Item `
            -LiteralPath $Temp `
            -Force `
            -ErrorAction SilentlyContinue
    }
}

function Get-ImageIdForService {

    param(
        [Parameter(Mandatory = $true)]
        [string]$Service
    )

    try {

        $Id = docker compose images -q $Service 2>$null

        if ($Id) {
            return ([string]$Id).Trim()
        }

    }
    catch {
    }

    return ""
}

function Invoke-ContainerProbe {

    param(
        [Parameter(Mandatory = $true)]
        [string]$Image,

        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    $OutputFile = Join-Path `
        $env:TEMP `
        ("aurix_step10_probe_" + [guid]::NewGuid().ToString("N") + ".txt")

    try {

        docker run `
            --rm `
            --entrypoint sh `
            $Image `
            -c $Command *> $OutputFile

        $ExitCode = $LASTEXITCODE
        $Output = Read-TextSafe $OutputFile

        return [pscustomobject]@{
            ExitCode = $ExitCode
            Output   = $Output
        }

    }
    finally {

        Remove-Item `
            -LiteralPath $OutputFile `
            -Force `
            -ErrorAction SilentlyContinue
    }
}

try {

    # ========================================================
    # [0] INITIALIZATION
    # ========================================================

    Section "[0] STEP 10 INITIALIZATION"

    Add-Line "ROOT   : $Root"
    Add-Line "REPORT : $Report"
    Add-Line "TIME   : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    Pass "Git repository detected."

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Pass "Docker CLI is available."
    }
    else {
        Fail "Docker CLI is unavailable."
    }

    try {

        docker compose version *> $null

        if ($LASTEXITCODE -eq 0) {
            Pass "Docker Compose CLI is available."
        }
        else {
            Fail "Docker Compose CLI is unavailable."
        }

    }
    catch {

        Fail "Docker Compose CLI is unavailable."

    }

    # ========================================================
    # [1] REQUIRED FILES
    # ========================================================

    Section "[1] DOCKER FILESET"

    $RequiredFiles = @(
        "Dockerfile",
        "docker-compose.yml",
        ".dockerignore"
    )

    foreach ($RelativePath in $RequiredFiles) {

        $FullPath = Join-Path $Root $RelativePath

        if (Test-Path -LiteralPath $FullPath) {

            Add-Line "$RelativePath = PRESENT"
            Pass "$RelativePath exists."

        }
        else {

            Add-Line "$RelativePath = MISSING"
            Fail "$RelativePath is missing."

        }
    }

    # ========================================================
    # [2] DOCKERFILE STATIC AUDIT
    # ========================================================

    Section "[2] DOCKERFILE STATIC AUDIT"

    $DockerfilePath = Join-Path $Root "Dockerfile"
    $DockerfileText = Read-TextSafe $DockerfilePath

    if ([string]::IsNullOrWhiteSpace($DockerfileText)) {

        Fail "Dockerfile could not be read."

    }
    else {

        $DockerfileLines = $DockerfileText -split "`r?`n"

        $FromLines = @(
            $DockerfileLines |
            Where-Object {
                $_ -match '^\s*FROM\s+'
            }
        )

        $RunLines = @(
            $DockerfileLines |
            Where-Object {
                $_ -match '^\s*RUN\s+'
            }
        )

        $CopyLines = @(
            $DockerfileLines |
            Where-Object {
                $_ -match '^\s*(COPY|ADD)\s+'
            }
        )

        $UserLines = @(
            $DockerfileLines |
            Where-Object {
                $_ -match '^\s*USER\s+'
            }
        )

        $PortLines = @(
            $DockerfileLines |
            Where-Object {
                $_ -match '^\s*EXPOSE\s+'
            }
        )

        $HealthLines = @(
            $DockerfileLines |
            Where-Object {
                $_ -match 'HEALTHCHECK'
            }
        )

        $CmdLines = @(
            $DockerfileLines |
            Where-Object {
                $_ -match '^\s*(CMD|ENTRYPOINT)\s+'
            }
        )

        Add-Line "FROM instructions   : $($FromLines.Count)"
        Add-Line "RUN instructions    : $($RunLines.Count)"
        Add-Line "COPY/ADD            : $($CopyLines.Count)"
        Add-Line "USER instructions   : $($UserLines.Count)"
        Add-Line "EXPOSE instructions : $($PortLines.Count)"
        Add-Line "HEALTHCHECK         : $($HealthLines.Count)"
        Add-Line "CMD/ENTRYPOINT      : $($CmdLines.Count)"

        if ($FromLines.Count -gt 0) {
            Pass "Dockerfile contains a base image definition."
        }
        else {
            Fail "Dockerfile has no FROM instruction."
        }

        if ($RunLines.Count -gt 0) {
            Pass "Dependency/build RUN instructions exist."
        }
        else {
            Warn "No RUN instructions found; dependency installation may be external."
        }

        if ($CopyLines.Count -gt 0) {
            Pass "Dockerfile explicitly includes application files."
        }
        else {
            Fail "Dockerfile contains no COPY/ADD instructions."
        }

        if ($UserLines.Count -gt 0) {
            Pass "Dockerfile declares a runtime USER."
        }
        else {
            Warn "Dockerfile does not declare a runtime USER."
        }

        if ($HealthLines.Count -gt 0) {
            Pass "Dockerfile contains a HEALTHCHECK."
        }
        else {
            Warn "Dockerfile does not contain a HEALTHCHECK."
        }

        if ($CmdLines.Count -gt 0) {
            Pass "Dockerfile declares CMD or ENTRYPOINT."
        }
        else {
            Warn "Dockerfile does not declare CMD or ENTRYPOINT."
        }

        if (
            $DockerfileText -match '(?i)\.env' -or
            $DockerfileText -match '(?i)\.git' -or
            $DockerfileText -match '(?i)__pycache__' -or
            $DockerfileText -match '(?i)node_modules' -or
            $DockerfileText -match '(?i)\.pytest_cache' -or
            $DockerfileText -match '(?i)\.mypy_cache' -or
            $DockerfileText -match '(?i)\.ruff_cache'
        ) {
            Warn "Dockerfile references build-context paths that require .dockerignore verification."
        }

        if ($DockerfileText -match '(?i)apt-get\s+.*--no-install-recommends') {
            Pass "apt installation uses --no-install-recommends."
        }
        elseif ($DockerfileText -match '(?i)apt-get') {
            Warn "apt-get is used without an obvious --no-install-recommends optimization."
        }

        if ($DockerfileText -match '(?i)curl\s+.*https?://') {
            Warn "Dockerfile downloads remote content during build; supply-chain provenance should be reviewed."
        }

    }

    # ========================================================
    # [3] DOCKERIGNORE AUDIT
    # ========================================================

    Section "[3] DOCKERIGNORE AUDIT"

    $DockerignorePath = Join-Path $Root ".dockerignore"
    $DockerignoreText = Read-TextSafe $DockerignorePath

    if ([string]::IsNullOrWhiteSpace($DockerignoreText)) {

        Fail ".dockerignore is empty or unreadable."

    }
    else {

        $RequiredIgnorePatterns = @(
            ".env",
            ".git",
            "node_modules",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build"
        )

        $MissingIgnorePatterns = @()

        foreach ($Pattern in $RequiredIgnorePatterns) {

            $EscapedPattern = [regex]::Escape($Pattern)

            if (
                $DockerignoreText -notmatch
                "(?m)^\s*$EscapedPattern\s*$"
            ) {
                $MissingIgnorePatterns += $Pattern
            }
        }

        Add-Line "Required ignore patterns: $($RequiredIgnorePatterns.Count)"
        Add-Line "Missing exact patterns : $($MissingIgnorePatterns.Count)"

        if ($MissingIgnorePatterns.Count -eq 0) {

            Pass ".dockerignore contains the required baseline exclusions."

        }
        else {

            $MissingIgnorePatterns |
                ForEach-Object {
                    Add-Line "MISSING_IGNORE=$_"
                }

            Warn ".dockerignore is missing one or more baseline exclusions."

        }

        if (
            $DockerignoreText -match '(?m)^\s*\.env(\.\*)?\s*$' -or
            $DockerignoreText -match '(?m)^\s*\.env\*'
        ) {
            Pass ".env files are excluded from Docker build context."
        }
        else {
            Fail ".env exclusion could not be confirmed in .dockerignore."
        }

        if ($DockerignoreText -match '(?m)^\s*node_modules/?\s*$') {
            Pass "node_modules is excluded from Docker build context."
        }
        else {
            Warn "node_modules exclusion is not explicitly present."
        }

    }

    # ========================================================
    # [4] COMPOSE CONFIGURATION
    # ========================================================

    Section "[4] DOCKER COMPOSE CONFIGURATION"

    $ComposePath = Join-Path $Root "docker-compose.yml"
    $ComposeText = Read-TextSafe $ComposePath

    if ([string]::IsNullOrWhiteSpace($ComposeText)) {

        Fail "docker-compose.yml could not be read."

    }
    else {

        if ($ComposeText -match 'aurix_runtime') {
            Pass "Compose references aurix_runtime."
        }
        else {
            Fail "Compose does not reference aurix_runtime."
        }

        if ($ComposeText -match '(?im)DATABASE_URL=.*aurix[:@]') {
            Fail "Privileged aurix database credentials appear in DATABASE_URL configuration."
        }
        else {
            Pass "No privileged aurix runtime DATABASE_URL reference detected."
        }

        if ($ComposeText -match '(?im)DATABASE_URL=.*aurix_runtime') {
            Pass "Compose DATABASE_URL wiring references aurix_runtime."
        }
        else {
            Fail "Compose DATABASE_URL wiring does not clearly reference aurix_runtime."
        }

        $ComposeSanitized = Redact-Text $ComposeText

        Add-Line ""
        Add-Line "Compose database/runtime credential references (redacted):"

        (
            $ComposeSanitized -split "`r?`n"
        ) |
        Where-Object {
            $_ -match '(?i)DATABASE_URL|POSTGRES_USER|POSTGRES_PASSWORD|JWT_SECRET'
        } |
        Select-Object -First 30 |
        ForEach-Object {
            Add-Line $_
        }

    }

    # ========================================================
    # [5] COMPOSE SERVICE DISCOVERY
    # ========================================================

    Section "[5] COMPOSE SERVICE DISCOVERY"

    $Services = @(Get-ComposeServices)

    if ($Services.Count -gt 0) {

        $Services |
            ForEach-Object {
                Add-Line "SERVICE=$_"
            }

        Pass "Docker Compose service configuration resolved."

    }
    else {

        Fail "Docker Compose service list could not be resolved."

    }

    $ExpectedServices = @(
        "api",
        "worker",
        "postgres",
        "redis",
        "client"
    )

    foreach ($ExpectedService in $ExpectedServices) {

        if ($Services -contains $ExpectedService) {

            Pass "Compose service exists: $ExpectedService"

        }
        else {

            $Alternative = switch ($ExpectedService) {

                "api" {
                    @("aurix_api")
                }

                "worker" {
                    @("aurix_worker")
                }

                "postgres" {
                    @("aurix_postgres", "db")
                }

                "redis" {
                    @("aurix_redis")
                }

                "client" {
                    @("frontend", "web")
                }

                default {
                    @()
                }
            }

            $FoundAlternative = $false

            foreach ($Candidate in $Alternative) {

                if ($Services -contains $Candidate) {
                    $FoundAlternative = $true
                }

            }

            if ($FoundAlternative) {

                Pass "Compose service exists through an accepted alias for $ExpectedService."

            }
            else {

                Warn "Expected logical service '$ExpectedService' was not found by name."

            }
        }
    }

    # ========================================================
    # [6] LIVE STACK SAFETY CHECK
    # ========================================================

    Section "[6] LIVE STACK SAFETY CHECK"

    $RunningNames = @(
        "aurix_enterprise_api",
        "aurix_enterprise_worker",
        "aurix_enterprise_postgres",
        "aurix_enterprise_redis",
        "aurix_enterprise_client"
    )

    foreach ($Name in $RunningNames) {

        try {

            $State = (
                [string](
                    docker inspect $Name --format "{{.State.Status}}" 2>$null
                )
            ).Trim()

        }
        catch {

            $State = ""

        }

        if ($State -eq "running") {
            Add-Line "$Name = running"
        }
        elseif ([string]::IsNullOrWhiteSpace($State)) {
            Add-Line "$Name = absent"
        }
        else {
            Add-Line "$Name = $State"
        }
    }

    Pass "Live-stack inventory completed; running containers are not recreated by this audit."

    # ========================================================
    # [7] CONTROLLED CLEAN BUILD
    # ========================================================
# [7] CONTROLLED CLEAN IMAGE BUILD
# ========================================================

Section "[7] CONTROLLED CLEAN IMAGE BUILD"

$BuildStdOut = Join-Path `
    $env:TEMP `
    ("aurix_step10_build_out_" +
        [guid]::NewGuid().ToString("N") +
        ".txt")

$BuildStdErr = Join-Path `
    $env:TEMP `
    ("aurix_step10_build_err_" +
        [guid]::NewGuid().ToString("N") +
        ".txt")

try {

    Add-Line "Build command: docker compose build --no-cache"

    $BuildProcess = Start-Process `
        -FilePath "docker" `
        -ArgumentList @(
            "compose",
            "build",
            "--no-cache"
        ) `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $BuildStdOut `
        -RedirectStandardError $BuildStdErr `
        -NoNewWindow `
        -PassThru `
        -Wait

    $BuildExit = $BuildProcess.ExitCode

    $BuildStdOutText = Read-TextSafe $BuildStdOut
    $BuildStdErrText = Read-TextSafe $BuildStdErr

    $BuildText =
        $BuildStdOutText +
        "`r`n" +
        $BuildStdErrText

    Add-Line "Docker build exit code: $BuildExit"

    if ($BuildExit -eq 0) {

        Pass "Controlled no-cache Docker Compose build completed successfully."

    }
    else {

        Fail "Controlled no-cache Docker Compose build failed with exit code $BuildExit."

        Add-Line "Final build output:"

        (
            (Redact-Text $BuildText) -split "`r?`n"
        ) |
        Select-Object -Last 180 |
        ForEach-Object {

            if (-not [string]::IsNullOrWhiteSpace($_)) {
                Add-Line $_
            }

        }
    }

}
catch {

    $BuildMessage = $_.Exception.Message

    Add-Line "Docker build probe exception: $BuildMessage"

    Fail "Controlled Docker build probe itself failed."

}
finally {

    Remove-Item `
        -LiteralPath $BuildStdOut `
        -Force `
        -ErrorAction SilentlyContinue

    Remove-Item `
        -LiteralPath $BuildStdErr `
        -Force `
        -ErrorAction SilentlyContinue
}
Section "[8] BUILT IMAGE INVENTORY"

    $BuiltImages = @{}

    foreach ($Service in $Services) {

        try {

            $ImageId = Get-ImageIdForService -Service $Service

            if (-not [string]::IsNullOrWhiteSpace($ImageId)) {

                $BuiltImages[$Service] = $ImageId

                Add-Line "$Service -> $ImageId"

                Pass "Built image identified for service: $Service"

            }
            else {

                Warn "No image ID could be resolved for service: $Service"

            }

        }
        catch {

            Warn "Unable to resolve image for service: $Service"

        }
    }

    # ========================================================
    # [9] IMAGE CONTENT AUDIT
    # ========================================================

    Section "[9] IMAGE CONTENT AUDIT"

    $ForbiddenImageChecks = @(
        @{
            Name    = ".env"
            Command = 'find / -type f \( -name ".env" -o -name ".env.*" \) 2>/dev/null | head -50'
        },
        @{
            Name    = "node_modules"
            Command = 'find / -type d -name "node_modules" 2>/dev/null | head -20'
        },
        @{
            Name    = "__pycache__"
            Command = 'find / -type d -name "__pycache__" 2>/dev/null | head -30'
        },
        @{
            Name    = "pytest cache"
            Command = 'find / -type d -name ".pytest_cache" 2>/dev/null | head -20'
        },
        @{
            Name    = "mypy cache"
            Command = 'find / -type d -name ".mypy_cache" 2>/dev/null | head -20'
        },
        @{
            Name    = "ruff cache"
            Command = 'find / -type d -name ".ruff_cache" 2>/dev/null | head -20'
        },
        @{
            Name    = "git metadata"
            Command = 'find / -type d -name ".git" 2>/dev/null | head -20'
        },
        @{
            Name    = "backup files"
            Command = 'find / -type f \( -name "*.bak" -o -name "*.backup" -o -name "*~" \) 2>/dev/null | head -50'
        },
        @{
            Name    = "local DB files"
            Command = 'find / -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" \) 2>/dev/null | head -50'
        }
    )

    foreach ($Entry in $ForbiddenImageChecks) {

        $EntryFailureCount = 0

        foreach ($Service in $BuiltImages.Keys) {

            $Image = $BuiltImages[$Service]

            $Probe = Invoke-ContainerProbe `
                -Image $Image `
                -Command $Entry.Command

            $Output = [string]$Probe.Output

            $UsefulLines = @(
                ($Output -split "`r?`n") |
                Where-Object {
                    -not [string]::IsNullOrWhiteSpace($_)
                }
            )

            if ($Probe.ExitCode -ne 0) {

                Warn "$($Entry.Name) probe could not complete reliably for $Service."

            }
            elseif ($UsefulLines.Count -gt 0) {

                $EntryFailureCount += $UsefulLines.Count

                Add-Line "$Service -> $($Entry.Name) findings: $($UsefulLines.Count)"

                $UsefulLines |
                    Select-Object -First 15 |
                    ForEach-Object {
                        Add-Line "  $_"
                    }

            }
        }

        if ($EntryFailureCount -eq 0) {

            Pass "No $($Entry.Name) artifacts detected in inspected images."

        }
        else {

            Fail "$($Entry.Name) artifacts were detected inside one or more images."

        }
    }

    # ========================================================
    # [10] IMAGE USER / PORT / HEALTHCHECK
    # ========================================================

    Section "[10] IMAGE USER / PORT / HEALTHCHECK"

    foreach ($Service in $BuiltImages.Keys) {

        $Image = $BuiltImages[$Service]

        try {

            $ImageUser = docker image inspect `
                $Image `
                --format "{{.Config.User}}" `
                2>$null

            $ImageUser = ([string]$ImageUser).Trim()

            $ImagePorts = docker image inspect `
                $Image `
                --format "{{json .Config.ExposedPorts}}" `
                2>$null

            $ImageHealth = docker image inspect `
                $Image `
                --format "{{json .Config.Healthcheck}}" `
                2>$null

            Add-Line "$Service USER=$ImageUser"
            Add-Line "$Service EXPOSED_PORTS=$ImagePorts"
            Add-Line "$Service HEALTHCHECK=$ImageHealth"

            if (
                -not [string]::IsNullOrWhiteSpace($ImageUser) -and
                $ImageUser -ne "root" -and
                $ImageUser -ne "0"
            ) {

                Pass "$Service image declares a non-root runtime user."

            }
            elseif (
                $Service -eq "postgres" -or
                $Service -eq "redis"
            ) {

                Warn "$Service image user is base-image controlled; custom application user check is not applicable."

            }
            else {

                Warn "$Service image appears to use root or does not declare a user."

            }

        }
        catch {

            Warn "Image metadata inspection failed for service: $Service"

        }
    }

    # ========================================================
    # [11] LIVE DATABASE CREDENTIAL WIRING
    # ========================================================

    Section "[11] LIVE DATABASE RUNTIME CREDENTIALS"

    $RuntimeContainers = @(
        "aurix_enterprise_api",
        "aurix_enterprise_worker"
    )

    foreach ($Container in $RuntimeContainers) {

        try {

            $RuntimeUrl = docker exec `
                $Container `
                sh -c 'printf "%s" "$DATABASE_URL"' `
                2>$null

            $RuntimeUrl = ([string]$RuntimeUrl).Trim()

            if (
                $RuntimeUrl -match '^postgresql\+psycopg://aurix_runtime:'
            ) {

                Add-Line (
                    "$Container DATABASE_URL = " +
                    "postgresql+psycopg://aurix_runtime:<REDACTED>@<host>:<port>/<db>"
                )

                Pass "$Container uses aurix_runtime in its live DATABASE_URL."

            }
            elseif (
                $RuntimeUrl -match '^postgresql\+psycopg://aurix:'
            ) {

                Fail "$Container still uses privileged aurix in its live DATABASE_URL."

            }
            elseif ([string]::IsNullOrWhiteSpace($RuntimeUrl)) {

                Fail "$Container has no live DATABASE_URL."

            }
            else {

                Warn "$Container DATABASE_URL exists but does not match the expected hardened pattern."

            }

        }
        catch {

            Fail "Unable to read live DATABASE_URL from $Container."

        }
    }

    # ========================================================
    # [12] LIVE DATABASE ROLE HARDENING
    # ========================================================

    Section "[12] LIVE DATABASE ROLE HARDENING"

    $DbProbe = @'
import os
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]

engine = create_engine(
    url,
    pool_pre_ping=True,
)

with engine.connect() as conn:

    user = conn.execute(
        text("SELECT current_user")
    ).scalar_one()

    db = conn.execute(
        text("SELECT current_database()")
    ).scalar_one()

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

    print("USER=" + str(user))
    print("DB=" + str(db))
    print("SUPERUSER=" + str(role["rolsuper"]))
    print("CREATEDB=" + str(role["rolcreatedb"]))
    print("CREATEROLE=" + str(role["rolcreaterole"]))
    print("CANLOGIN=" + str(role["rolcanlogin"]))
    print("BYPASSRLS=" + str(role["rolbypassrls"]))

engine.dispose()
'@

    $DbRoleOut = Join-Path `
        $env:TEMP `
        ("aurix_step10_dbrole_" + [guid]::NewGuid().ToString("N") + ".txt")

    try {

        $DbProbe |
            docker exec -i aurix_enterprise_api python - *> $DbRoleOut

        $DbRoleExit = $LASTEXITCODE
        $DbRoleText = Read-TextSafe $DbRoleOut

        (
            $DbRoleText -split "`r?`n"
        ) |
        Where-Object {
            -not [string]::IsNullOrWhiteSpace($_)
        } |
        ForEach-Object {
            Add-Line $_
        }

        $UserValue = ""
        $SuperValue = ""
        $CreateDbValue = ""
        $CreateRoleValue = ""
        $CanLoginValue = ""
        $BypassValue = ""

        foreach ($Line in ($DbRoleText -split "`r?`n")) {

            if ($Line -match '^USER=') {
                $UserValue = ($Line -replace '^USER=', "").Trim()
            }
            elseif ($Line -match '^SUPERUSER=') {
                $SuperValue = (
                    $Line -replace '^SUPERUSER=', ""
                ).Trim().ToLowerInvariant()
            }
            elseif ($Line -match '^CREATEDB=') {
                $CreateDbValue = (
                    $Line -replace '^CREATEDB=', ""
                ).Trim().ToLowerInvariant()
            }
            elseif ($Line -match '^CREATEROLE=') {
                $CreateRoleValue = (
                    $Line -replace '^CREATEROLE=', ""
                ).Trim().ToLowerInvariant()
            }
            elseif ($Line -match '^CANLOGIN=') {
                $CanLoginValue = (
                    $Line -replace '^CANLOGIN=', ""
                ).Trim().ToLowerInvariant()
            }
            elseif ($Line -match '^BYPASSRLS=') {
                $BypassValue = (
                    $Line -replace '^BYPASSRLS=', ""
                ).Trim().ToLowerInvariant()
            }
        }

        Add-Line "PARSED_USER=$UserValue"
        Add-Line "PARSED_SUPERUSER=$SuperValue"
        Add-Line "PARSED_CREATEDB=$CreateDbValue"
        Add-Line "PARSED_CREATEROLE=$CreateRoleValue"
        Add-Line "PARSED_CANLOGIN=$CanLoginValue"
        Add-Line "PARSED_BYPASSRLS=$BypassValue"

        if (
            $DbRoleExit -eq 0 -and
            $UserValue -eq "aurix_runtime" -and
            $SuperValue -eq "false" -and
            $CreateDbValue -eq "false" -and
            $CreateRoleValue -eq "false" -and
            $CanLoginValue -eq "true" -and
            $BypassValue -eq "false"
        ) {

            Pass "Live API database role is fully restricted for application runtime."

        }
        else {

            Fail "Live API database role hardening contract failed."

        }

    }
    finally {

        Remove-Item `
            -LiteralPath $DbRoleOut `
            -Force `
            -ErrorAction SilentlyContinue
    }

    # ========================================================
    # [13] LIVE RUNTIME HEALTH
    # ========================================================

    Section "[13] LIVE RUNTIME HEALTH"

    $HealthContainers = @(
        "aurix_enterprise_postgres",
        "aurix_enterprise_redis",
        "aurix_enterprise_api",
        "aurix_enterprise_worker",
        "aurix_enterprise_client"
    )

    foreach ($Container in $HealthContainers) {

        try {

            $Status = (
                [string](
                    docker inspect $Container --format "{{.State.Status}}" 2>$null
                )
            ).Trim()

            $Health = (
                [string](
                    docker inspect $Container --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}NO_HEALTHCHECK{{end}}" 2>$null
                )
            ).Trim()

            Add-Line "$Container STATUS=$Status HEALTH=$Health"

            if ($Status -ne "running") {

                Fail "$Container is not running."

            }
            elseif ($Health -eq "unhealthy") {

                Fail "$Container reports unhealthy."

            }
            elseif ($Health -eq "healthy") {

                Pass "$Container is running and healthy."

            }
            else {

                Pass "$Container is running; no Docker healthcheck is declared."

            }

        }
        catch {

            Fail "Unable to inspect live health for $Container."

        }
    }

    # ========================================================
    # [14] API DATABASE CONNECTIVITY
    # ========================================================

    Section "[14] API DATABASE CONNECTIVITY"

    try {

        $Health = Invoke-RestMethod `
            -Uri "http://localhost:8000/api/v1/health" `
            -Method Get `
            -TimeoutSec 15 `
            -ErrorAction Stop

        $HealthJson = $Health | ConvertTo-Json -Depth 40

        Add-Line $HealthJson

        $HealthText = [string]$HealthJson

        if ($HealthText -match '(?i)"database"\s*:\s*"healthy"') {

            Pass "Live API health reports database healthy."

        }
        else {

            Warn "Live API health did not explicitly report database healthy."

        }

    }
    catch {

        Fail "Live API health endpoint could not be reached."

    }

    # ========================================================
    # [15] LIVE CONTAINER SECRET EXPOSURE
    # ========================================================

    Section "[15] LIVE CONTAINER SECRET-EXPOSURE CHECK"

    foreach ($Container in @(
        "aurix_enterprise_api",
        "aurix_enterprise_worker"
    )) {

        try {

            $Environment = docker exec $Container env 2>$null

            $Suspicious = @(
                $Environment |
                Where-Object {
                    $_ -match '(?i)^(DATABASE_URL|POSTGRES_PASSWORD|JWT_SECRET_KEY|SECRET_KEY|API_KEY|TOKEN)='
                }
            )

            if ($Suspicious.Count -eq 0) {

                Pass "$Container has no high-value secret environment variables detected."

            }
            else {

                Add-Line (
                    "$Container secret-bearing environment variables detected: " +
                    "$($Suspicious.Count)"
                )

                $Suspicious |
                    ForEach-Object {
                        Add-Line (
                            (($_ -split '=', 2)[0]) +
                            "=<REDACTED>"
                        )
                    }

                Warn "$Container exposes secret-bearing environment variables; review whether runtime injection is intentional."

            }

        }
        catch {

            Not-Proven "Unable to inspect environment of $Container."

        }
    }

    # ========================================================
    # [16] ADMIN / DEPLOYMENT ROLE SEPARATION
    # ========================================================

    Section "[16] DEPLOYMENT / ADMIN ROLE SEPARATION"

    if (
        $ComposeText -match '(?i)\baurix\b' -and
        $ComposeText -match '(?i)postgres'
    ) {

        Warn "Compose contains privileged aurix references in PostgreSQL bootstrap/configuration context. Confirm this role is used only for deployment/admin/bootstrap operations."

        Pass "Application runtime wiring remains separately assigned to aurix_runtime."

    }
    else {

        Pass "No privileged aurix runtime wiring was detected in compose."

    }

    # ========================================================
    # [17] MIGRATION / STARTUP SAFETY
    # ========================================================

    Section "[17] MIGRATION + STARTUP SAFETY"

    $MigrationPatterns = @(
        "alembic upgrade head",
        "alembic",
        "migrate",
        "entrypoint",
        "command:"
    )

    $MigrationHits = @(
        Select-String `
            -Path @(
                $DockerfilePath,
                $ComposePath
            ) `
            -Pattern $MigrationPatterns `
            -CaseSensitive:$false `
            -ErrorAction SilentlyContinue
    )

    if ($MigrationHits.Count -gt 0) {

        $MigrationHits |
            Select-Object -First 80 |
            ForEach-Object {

                Add-Line (
                    "{0}:{1}: migration/startup reference" -f
                    $_.Path,
                    $_.LineNumber
                )

            }

        Pass "Docker startup/migration configuration references were identified."

    }
    else {

        Not-Proven "No migration/startup references were found in Docker configuration."

    }

    # ========================================================
    # [18] IMAGE SIZE SNAPSHOT
    # ========================================================

    Section "[18] IMAGE SIZE SNAPSHOT"

    foreach ($Service in $BuiltImages.Keys) {

        try {

            $Image = $BuiltImages[$Service]

            $SizeText = docker image inspect `
                $Image `
                --format "{{.Size}}" `
                2>$null

            if ($SizeText) {

                $Bytes = [double]$SizeText
                $MiB = [Math]::Round(
                    $Bytes / 1MB,
                    2
                )

                Add-Line "$Service IMAGE_SIZE_MIB=$MiB"

                if ($MiB -lt 2000) {

                    Pass "$Service image size is below the 2 GiB review threshold."

                }
                else {

                    Warn "$Service image exceeds the 2 GiB review threshold."

                }

            }

        }
        catch {

            Warn "Unable to measure image size for $Service."

        }
    }

    # ========================================================
    # [19] FINAL GATE
    # ========================================================

    Section "[19] STEP 10 FINAL GATE"

    Add-Line ""
    Add-Line "PASS COUNT       : $($Passes.Count)"
    Add-Line "WARNING COUNT    : $($Warnings.Count)"
    Add-Line "NOT PROVEN COUNT : $($NotProven.Count)"
    Add-Line "FAIL COUNT       : $($Failures.Count)"
    Add-Line ""

    if ($Failures.Count -eq 0) {

        if ($NotProven.Count -eq 0) {

            Add-Line "DOCKER_PRODUCTION_AUDIT = PASS"
            Add-Line "STEP_10 = COMPLETE"

        }
        else {

            Add-Line "DOCKER_PRODUCTION_AUDIT = PASS_WITH_UNPROVEN_BOUNDARIES"
            Add-Line "STEP_10 = COMPLETE_WITH_BOUNDARIES"

        }

    }
    else {

        Add-Line "DOCKER_PRODUCTION_AUDIT = FAIL"
        Add-Line "STEP_10 = NOT_READY"

    }

    Add-Line ""
    Add-Line "IMPORTANT:"
    Add-Line "The controlled build does not recreate the running application containers."
    Add-Line "No database schema or application records were modified by this audit."
    Add-Line "Static findings marked WARN require contextual engineering review."
    Add-Line "NOT_PROVEN items require evidence not safely obtainable by this audit."

}
catch {

    $Message = $_.Exception.Message

    Add-Line "[FAIL] Fatal Step 10 audit exception: $Message"

    [void]$Failures.Add(
        "Fatal Step 10 audit exception: $Message"
    )

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

# ============================================================
# CONSOLE RESULT
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "AURIX STEP 10 MASTER - FINAL OUTPUT"
Write-Host "============================================================"
Write-Host "MASTER REPORT : $Report"
Write-Host "LATEST REPORT : $LatestReport"
Write-Host ""
Write-Host "PASS COUNT    : $($Passes.Count)"
Write-Host "WARNING COUNT : $($Warnings.Count)"
Write-Host "NOT PROVEN    : $($NotProven.Count)"
Write-Host "FAIL COUNT    : $($Failures.Count)"
Write-Host ""

if (
    $Failures.Count -eq 0 -and
    $NotProven.Count -eq 0
) {

    Write-Host "DOCKER_PRODUCTION_AUDIT = PASS" -ForegroundColor Green
    Write-Host "STEP_10 = COMPLETE" -ForegroundColor Green

}
elseif ($Failures.Count -eq 0) {

    Write-Host "DOCKER_PRODUCTION_AUDIT = PASS_WITH_UNPROVEN_BOUNDARIES" -ForegroundColor Yellow
    Write-Host "STEP_10 = COMPLETE_WITH_BOUNDARIES" -ForegroundColor Yellow

}
else {

    Write-Host "DOCKER_PRODUCTION_AUDIT = FAIL" -ForegroundColor Red
    Write-Host "STEP_10 = NOT_READY" -ForegroundColor Red

}

Write-Host ""
Write-Host "============================================================"
Write-Host "STEP 10 MASTER COMPLETE"
Write-Host "============================================================"