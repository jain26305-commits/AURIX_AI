$ErrorActionPreference = "Stop"

# ============================================================
# AURIX STEP 11 MASTER
# RELEASE CANDIDATE FREEZE
#
# PURPOSE
# -------
# Establish one deterministic release identity containing:
#
#   * backend version
#   * frontend version
#   * schema version
#   * migration head
#   * dependency fingerprints
#   * exact Git commit
#   * Docker image identity
#   * Docker image digest
#   * configuration contract
#   * release timestamp
#
# RELEASE PRINCIPLE
# -----------------
# A release candidate must identify the exact source tree,
# dependency state, migration head, Docker image identities and
# configuration contract represented by the release.
#
# SAFETY
# ------
# * No database writes
# * No schema changes
# * No migrations executed
# * No application records inserted
# * No container recreation
# * No docker compose up/down
# * No image rebuild
# * No secrets printed
# * Release manifest is generated only under AURIX_STEP11
# ============================================================

$Root = (Get-Location).Path

if (-not (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
    throw "Git repository not detected. Run this from the AURIX repository root."
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ReleaseDir = Join-Path $Root "AURIX_STEP11"

New-Item `
    -ItemType Directory `
    -Path $ReleaseDir `
    -Force |
    Out-Null

$Report = Join-Path `
    $ReleaseDir `
    "AURIX_STEP11_RELEASE_CANDIDATE_AUDIT_$Timestamp.txt"

$LatestReport = Join-Path `
    $Root `
    "AURIX_STEP11_RELEASE_CANDIDATE_AUDIT.txt"

$Manifest = Join-Path `
    $ReleaseDir `
    "AURIX_RELEASE_MANIFEST_$Timestamp.json"

$LatestManifest = Join-Path `
    $Root `
    "AURIX_RELEASE_MANIFEST.json"

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
        return Get-Content `
            -LiteralPath $Path `
            -Raw `
            -ErrorAction Stop
    }
    catch {
        return ""
    }
}

function Get-GitOutput {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    try {

        $Value = & git @Arguments 2>$null

        if ($LASTEXITCODE -eq 0) {
            return ([string]$Value).Trim()
        }

    }
    catch {
    }

    return ""
}

function Get-Hash {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    try {
        return (
            Get-FileHash `
                -LiteralPath $Path `
                -Algorithm SHA256 `
                -ErrorAction Stop
        ).Hash
    }
    catch {
        return ""
    }
}

function Get-JsonPropertyValue {
    param(
        [Parameter(Mandatory = $true)]
        $Object,

        [Parameter(Mandatory = $true)]
        [string[]]$Names
    )

    foreach ($Name in $Names) {

        $Property = $Object.PSObject.Properties |
            Where-Object {
                $_.Name -ieq $Name
            } |
            Select-Object -First 1

        if ($null -ne $Property) {

            $Value = $Property.Value

            if ($null -ne $Value -and
                -not [string]::IsNullOrWhiteSpace([string]$Value)
            ) {
                return [string]$Value
            }

        }
    }

    return ""
}

function Get-NodeVersionFromPackage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackagePath
    )

    $Text = Read-TextSafe $PackagePath

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return ""
    }

    try {

        $Json = $Text | ConvertFrom-Json

        $Version = Get-JsonPropertyValue `
            -Object $Json `
            -Names @(
                "version"
            )

        return $Version

    }
    catch {

        return ""

    }
}

function Get-PythonVersionFromProject {
    param(
        [string]$PyProjectPath,
        [string]$SetupPath,
        [string]$RequirementsPath
    )

    # --------------------------------------------------------
    # pyproject.toml
    # --------------------------------------------------------

    if (
        -not [string]::IsNullOrWhiteSpace($PyProjectPath) -and
        (Test-Path -LiteralPath $PyProjectPath)
    ) {

        $Text = Read-TextSafe $PyProjectPath

        if (-not [string]::IsNullOrWhiteSpace([string]$Text)) {

            $SafeText = [string]$Text

            $Match = [regex]::Match(
                $SafeText,
                '(?mi)^\s*version\s*=\s*["'']([^"'']+)["'']'
            )

            if ($Match.Success) {
                return [string]$Match.Groups[1].Value.Trim()
            }
        }
    }

    # --------------------------------------------------------
    # setup.py / setup.cfg
    # --------------------------------------------------------

    if (
        -not [string]::IsNullOrWhiteSpace($SetupPath) -and
        (Test-Path -LiteralPath $SetupPath)
    ) {

        $Text = Read-TextSafe $SetupPath

        if (-not [string]::IsNullOrWhiteSpace([string]$Text)) {

            $SafeText = [string]$Text

            $Match = [regex]::Match(
                $SafeText,
                '(?mi)version\s*=\s*["'']([^"'']+)["'']'
            )

            if ($Match.Success) {
                return [string]$Match.Groups[1].Value.Trim()
            }
        }
    }

    # --------------------------------------------------------
    # No reliable backend version available.
    # Return empty string instead of throwing.
    # --------------------------------------------------------

    return ""
}
function Get-MigrationRevisions {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AlembicDir
    )

    $MigrationFiles = @()

    if (Test-Path -LiteralPath $AlembicDir) {

        $MigrationFiles = @(
            Get-ChildItem `
                -LiteralPath $AlembicDir `
                -Recurse `
                -File `
                -Filter "*.py" `
                -ErrorAction SilentlyContinue
        )
    }

    $Revisions = [System.Collections.Generic.List[object]]::new()

    foreach ($File in $MigrationFiles) {

        $Text = Read-TextSafe $File.FullName

        if ([string]::IsNullOrWhiteSpace($Text)) {
            continue
        }

        $RevisionMatch = [regex]::Match(
            $Text,
            '(?m)^\s*revision\s*=\s*["'']([^"'']+)["'']'
        )

        $DownMatch = [regex]::Match(
            $Text,
            '(?m)^\s*down_revision\s*=\s*(.+?)\s*$'
        )

        if (-not $RevisionMatch.Success) {
            continue
        }

        $Revision = $RevisionMatch.Groups[1].Value.Trim()

        $DownRevision = ""

        if ($DownMatch.Success) {

            $RawDown = $DownMatch.Groups[1].Value.Trim()

            if ($RawDown -match '^["'']([^"'']+)["'']$') {
                $DownRevision = $Matches[1]
            }
            elseif ($RawDown -eq "None") {
                $DownRevision = ""
            }
            else {
                $DownRevision = $RawDown
            }
        }

        $Revisions.Add(
            [pscustomobject]@{
                File         = $File.FullName
                Revision     = $Revision
                DownRevision = $DownRevision
            }
        )

    }

    return @($Revisions)
}

function Get-DockerImageDigest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Image
    )

    try {

        $RepoDigests = @(
            docker image inspect `
                $Image `
                --format "{{json .RepoDigests}}" `
                2>$null |
            ConvertFrom-Json
        )

        if ($RepoDigests.Count -gt 0) {

            foreach ($Digest in $RepoDigests) {

                if (
                    [string]$Digest -match '@sha256:[a-f0-9]{64}'
                ) {
                    return [string]$Digest
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

    Section "[0] STEP 11 INITIALIZATION"

    Add-Line "ROOT          : $Root"
    Add-Line "REPORT        : $Report"
    Add-Line "MANIFEST      : $Manifest"
    Add-Line "TIMESTAMP     : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ssK')"

    Pass "Git repository detected."

    if (Get-Command git -ErrorAction SilentlyContinue) {
        Pass "Git CLI is available."
    }
    else {
        Fail "Git CLI is unavailable."
    }

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Pass "Docker CLI is available."
    }
    else {
        Fail "Docker CLI is unavailable."
    }

    # ========================================================
    # [1] GIT RELEASE IDENTITY
    # ========================================================

    Section "[1] GIT RELEASE IDENTITY"

    $GitSha = Get-GitOutput `
        -Arguments @(
            "rev-parse",
            "HEAD"
        )

    $GitShortSha = Get-GitOutput `
        -Arguments @(
            "rev-parse",
            "--short=12",
            "HEAD"
        )

    $GitBranch = Get-GitOutput `
        -Arguments @(
            "branch",
            "--show-current"
        )

    $GitTag = Get-GitOutput `
        -Arguments @(
            "describe",
            "--tags",
            "--exact-match",
            "HEAD"
        )

    $GitStatus = Get-GitOutput `
        -Arguments @(
            "status",
            "--porcelain"
        )

    $GitCommitDate = Get-GitOutput `
        -Arguments @(
            "show",
            "-s",
            "--format=%cI",
            "HEAD"
        )

    Add-Line "GIT_SHA        : $GitSha"
    Add-Line "GIT_SHORT_SHA  : $GitShortSha"
    Add-Line "GIT_BRANCH     : $GitBranch"
    Add-Line "GIT_TAG        : $GitTag"
    Add-Line "GIT_COMMIT_DATE: $GitCommitDate"

    if (
        -not [string]::IsNullOrWhiteSpace($GitSha) -and
        $GitSha -match '^[0-9a-f]{40}$'
    ) {

        Pass "Exact 40-character Git commit SHA captured."

    }
    else {

        Fail "Exact Git commit SHA could not be established."

    }

    if ([string]::IsNullOrWhiteSpace($GitStatus)) {

        Pass "Git working tree is clean."

    }
    else {

        Add-Line "Git working tree changes detected."
        Add-Line $GitStatus

        Warn "Working tree is not clean; release reproducibility requires review."

    }

    if (-not [string]::IsNullOrWhiteSpace($GitTag)) {

        Pass "HEAD is associated with an exact Git tag."

    }
    else {

        Warn "HEAD has no exact tag; release will use the immutable Git SHA."

    }

    # ========================================================
    # [2] BACKEND VERSION
    # ========================================================

    # ========================================================
# [2] BACKEND VERSION
# ========================================================

    # ========================================================
    # [2] BACKEND VERSION
    # ========================================================

    Section "[2] BACKEND VERSION"

    $BackendVersion = ""

    $PyProjectPath = Join-Path $Root "pyproject.toml"
    $SetupPath = Join-Path $Root "setup.py"
    $SettingsPath = Join-Path $Root "aurix_core\config\settings.py"

    # --------------------------------------------------------
    # 1. pyproject.toml
    # --------------------------------------------------------

    if (Test-Path -LiteralPath $PyProjectPath) {

        $Text = Read-TextSafe $PyProjectPath

        if (-not [string]::IsNullOrWhiteSpace([string]$Text)) {

            $Match = [regex]::Match(
                [string]$Text,
                '(?mi)^\s*version\s*=\s*["'']([^"'']+)["'']'
            )

            if ($Match.Success) {

                $BackendVersion = (
                    [string]$Match.Groups[1].Value
                ).Trim()

            }
        }
    }

    # --------------------------------------------------------
    # 2. setup.py
    # --------------------------------------------------------

    if (
        [string]::IsNullOrWhiteSpace($BackendVersion) -and
        (Test-Path -LiteralPath $SetupPath)
    ) {

        $Text = Read-TextSafe $SetupPath

        if (-not [string]::IsNullOrWhiteSpace([string]$Text)) {

            $Match = [regex]::Match(
                [string]$Text,
                '(?mi)version\s*=\s*["'']([^"'']+)["'']'
            )

            if ($Match.Success) {

                $BackendVersion = (
                    [string]$Match.Groups[1].Value
                ).Trim()

            }
        }
    }

    # --------------------------------------------------------
    # 3. settings.py build_version
    #
    # This is the authoritative AURIX application version
    # when packaging metadata is absent.
    # --------------------------------------------------------

    if (
        [string]::IsNullOrWhiteSpace($BackendVersion) -and
        (Test-Path -LiteralPath $SettingsPath)
    ) {

        $SettingsText = Read-TextSafe $SettingsPath

        if (-not [string]::IsNullOrWhiteSpace([string]$SettingsText)) {

            # Handles:
            # build_version: str = Field(default="16.0.0", ...)
            $Match = [regex]::Match(
                [string]$SettingsText,
                '(?mi)^\s*build_version\s*:\s*[^=]+=\s*Field\(\s*default\s*=\s*["'']([^"'']+)["'']'
            )

            if (-not $Match.Success) {

                # Handles:
                # build_version: str = "16.0.0"
                $Match = [regex]::Match(
                    [string]$SettingsText,
                    '(?mi)^\s*build_version\s*:\s*[^=]+=\s*["'']([^"'']+)["'']'
                )

            }

            if (-not $Match.Success) {

                # Handles:
                # build_version = "16.0.0"
                $Match = [regex]::Match(
                    [string]$SettingsText,
                    '(?mi)^\s*build_version\s*=\s*["'']([^"'']+)["'']'
                )

            }

            if ($Match.Success) {

                $BackendVersion = (
                    [string]$Match.Groups[1].Value
                ).Trim()

            }
        }
    }

    # --------------------------------------------------------
    # 4. __version__ fallback
    # --------------------------------------------------------

    if ([string]::IsNullOrWhiteSpace($BackendVersion)) {

        $BackendVersionCandidates = @(
            "aurix_api\__init__.py",
            "aurix_core\__init__.py",
            "api\__init__.py"
        )

        foreach ($Candidate in $BackendVersionCandidates) {

            $Path = Join-Path $Root $Candidate

            if (-not (Test-Path -LiteralPath $Path)) {
                continue
            }

            $Text = Read-TextSafe $Path

            if ([string]::IsNullOrWhiteSpace([string]$Text)) {
                continue
            }

            $Match = [regex]::Match(
                [string]$Text,
                '(?mi)^\s*__version__\s*=\s*["'']([^"'']+)["'']'
            )

            if ($Match.Success) {

                $BackendVersion = (
                    [string]$Match.Groups[1].Value
                ).Trim()

                break

            }
        }
    }

    # --------------------------------------------------------
    # 5. Final classification
    # --------------------------------------------------------

    if (-not [string]::IsNullOrWhiteSpace($BackendVersion)) {

        Add-Line "BACKEND_VERSION=$BackendVersion"
        Pass "Backend runtime build version identified."

    }
    else {

        Not-Proven "Backend semantic version could not be identified automatically."

    }

Section "[3] FRONTEND VERSION"

    $PackageCandidates = @(
        (Join-Path $Root "aurix_client\package.json"),
        (Join-Path $Root "package.json")
    )

    $FrontendVersion = ""

    foreach ($PackagePath in $PackageCandidates) {

        if (-not (Test-Path -LiteralPath $PackagePath)) {
            continue
        }

        $FrontendVersion = Get-NodeVersionFromPackage `
            -PackagePath $PackagePath

        if (-not [string]::IsNullOrWhiteSpace($FrontendVersion)) {
            Add-Line "FRONTEND_PACKAGE=$PackagePath"
            break
        }

    }

    if (-not [string]::IsNullOrWhiteSpace($FrontendVersion)) {

        Add-Line "FRONTEND_VERSION=$FrontendVersion"
        Pass "Frontend version identified from package metadata."

    }
    else {

        Not-Proven "Frontend semantic version could not be identified automatically."

    }

    # ========================================================
    # [4] SCHEMA / ALEMBIC VERSION
    # ========================================================

    Section "[4] SCHEMA VERSION + MIGRATION HEAD"

    $AlembicDir = Join-Path $Root "alembic\versions"

    if (-not (Test-Path -LiteralPath $AlembicDir)) {

        Fail "alembic/versions directory was not found."

        $MigrationRows = @()

    }
    else {

        $MigrationRows = Get-MigrationRevisions `
            -AlembicDir $AlembicDir

    }

    Add-Line "Migration files discovered: $($MigrationRows.Count)"

    $RevisionMap = @{}

    foreach ($Row in $MigrationRows) {
        $RevisionMap[$Row.Revision] = $Row
    }

    $DownRevisions = New-Object System.Collections.Generic.HashSet[string]

    foreach ($Row in $MigrationRows) {

        if (-not [string]::IsNullOrWhiteSpace($Row.DownRevision)) {

            [void]$DownRevisions.Add(
                $Row.DownRevision
            )

        }
    }

    $MigrationHeads = @(
        $MigrationRows |
        Where-Object {
            -not $DownRevisions.Contains($_.Revision)
        }
    )

    Add-Line "Migration heads detected: $($MigrationHeads.Count)"

    if ($MigrationHeads.Count -eq 1) {

        $MigrationHead = [string]$MigrationHeads[0].Revision

        Add-Line "MIGRATION_HEAD=$MigrationHead"

        Pass "Exactly one Alembic migration head was detected."

    }
    elseif ($MigrationHeads.Count -gt 1) {

        foreach ($Head in $MigrationHeads) {
            Add-Line "MULTIPLE_HEAD=$($Head.Revision)"
        }

        Fail "Multiple Alembic migration heads were detected."

        $MigrationHead = ""

    }
    else {

        Fail "No Alembic migration head could be derived."

        $MigrationHead = ""

    }

    # Determine the apparent schema version from the latest numeric
    # migration filename when possible, but do not claim this is the
    # database's live schema version.
    $NumericMigrationVersions = @()

    foreach ($Row in $MigrationRows) {

        $FileName = Split-Path `
            $Row.File `
            -Leaf

        $Match = [regex]::Match(
            $FileName,
            '^(\d+)_'
        )

        if ($Match.Success) {

            $NumericMigrationVersions += [int]$Match.Groups[1].Value

        }
    }

    if ($NumericMigrationVersions.Count -gt 0) {

        $SchemaVersion = (
            $NumericMigrationVersions |
            Sort-Object |
            Select-Object -Last 1
        )

        Add-Line "SCHEMA_VERSION_NUMERIC=$SchemaVersion"
        Pass "Latest numeric migration version was derived from the migration filenames."

    }
    else {

        $SchemaVersion = ""

        Not-Proven "Numeric schema version could not be derived from migration filenames."

    }

    # ========================================================
    # [5] DEPENDENCY FINGERPRINTS
    # ========================================================

    Section "[5] DEPENDENCY VERSION / FINGERPRINT AUDIT"

    $DependencyFiles = @(
        "requirements.txt",
        "requirements.lock",
        "poetry.lock",
        "uv.lock",
        "Pipfile.lock",
        "package-lock.json",
        "npm-shrinkwrap.json",
        "yarn.lock",
        "pnpm-lock.yaml"
    )

    $DependencyFingerprints = [ordered]@{}

    foreach ($RelativePath in $DependencyFiles) {

        $Path = Join-Path $Root $RelativePath

        if (Test-Path -LiteralPath $Path) {

            $Hash = Get-Hash $Path

            if (-not [string]::IsNullOrWhiteSpace($Hash)) {

                $DependencyFingerprints[$RelativePath] = $Hash

                Add-Line "$RelativePath SHA256=$Hash"

                Pass "Dependency lock/fingerprint captured: $RelativePath"

            }
            else {

                Warn "Could not hash dependency file: $RelativePath"

            }

        }
    }

    if ($DependencyFingerprints.Count -eq 0) {

        Not-Proven "No dependency lock/fingerprint files were found."

    }

    # ========================================================
    # [6] DOCKER SERVICE / IMAGE IDENTITY
    # ========================================================

    Section "[6] DOCKER SERVICE + IMAGE IDENTITY"

    $ComposePath = Join-Path $Root "docker-compose.yml"
    $ComposeText = Read-TextSafe $ComposePath

    if ([string]::IsNullOrWhiteSpace($ComposeText)) {

        Fail "docker-compose.yml could not be read."

    }
    else {

        try {

            $ComposeServicesTemp = Join-Path `
                $env:TEMP `
                ("aurix_step11_services_" +
                    [guid]::NewGuid().ToString("N") +
                    ".txt")

            docker compose config --services *> $ComposeServicesTemp

            $ComposeServices = @(
                Get-Content `
                    -LiteralPath $ComposeServicesTemp |
                Where-Object {
                    -not [string]::IsNullOrWhiteSpace($_)
                }
            )

            Remove-Item `
                -LiteralPath $ComposeServicesTemp `
                -Force `
                -ErrorAction SilentlyContinue

        }
        catch {

            $ComposeServices = @()

        }

        if ($ComposeServices.Count -gt 0) {

            Pass "Docker Compose service topology resolved."

        }
        else {

            Fail "Docker Compose services could not be resolved."

        }
    }

    $ReleaseImages = [ordered]@{}

    foreach ($Service in $ComposeServices) {

        try {

            $Image = docker compose images -q $Service 2>$null

            $Image = ([string]$Image).Trim()

            if ([string]::IsNullOrWhiteSpace($Image)) {

                Warn "No image ID could be resolved for Compose service: $Service"
                continue

            }

            $Repo = docker compose images $Service 2>$null |
                Select-Object -Skip 1 |
                Select-Object -First 1

            $Repo = ([string]$Repo).Trim()

            $Digest = Get-DockerImageDigest `
                -Image $Image

            $ImageSize = docker image inspect `
                $Image `
                --format "{{.Size}}" `
                2>$null

            $SizeMiB = ""

            if ($ImageSize) {

                try {

                    $SizeMiB = [Math]::Round(
                        ([double]$ImageSize) / 1MB,
                        2
                    )

                }
                catch {
                    $SizeMiB = ""
                }
            }

            $ReleaseImages[$Service] = [ordered]@{
                image_id  = $Image
                repo      = $Repo
                digest    = $Digest
                size_mib  = $SizeMiB
            }

            Add-Line "$Service IMAGE_ID=$Image"

            if (-not [string]::IsNullOrWhiteSpace($Digest)) {

                Add-Line "$Service DIGEST=$Digest"

                Pass "Immutable Docker digest captured for service: $Service"

            }
            else {

                Warn "Repository digest is unavailable for service: $Service"

            }

        }
        catch {

            Warn "Unable to resolve Docker image identity for service: $Service"

        }
    }

    if ($ReleaseImages.Count -gt 0) {

        Pass "Docker image identity captured for available services."

    }
    else {

        Not-Proven "No live/built Compose image identities could be captured."

    }

    # ========================================================
    # [7] LIVE CONTAINER COMMIT / IMAGE CONSISTENCY
    # ========================================================

    Section "[7] LIVE CONTAINER IMAGE CONSISTENCY"

    $KnownContainerMap = @(
        [pscustomobject]@{
            Name    = "aurix_enterprise_api"
            Logical = "api"
        },
        [pscustomobject]@{
            Name    = "aurix_enterprise_worker"
            Logical = "worker"
        },
        [pscustomobject]@{
            Name    = "aurix_enterprise_postgres"
            Logical = "postgres"
        },
        [pscustomobject]@{
            Name    = "aurix_enterprise_redis"
            Logical = "redis"
        },
        [pscustomobject]@{
            Name    = "aurix_enterprise_client"
            Logical = "client"
        }
    )

    $LiveContainers = [ordered]@{}

    foreach ($Entry in $KnownContainerMap) {

        try {

            $ContainerId = docker inspect `
                $Entry.Name `
                --format "{{.Id}}" `
                2>$null

            if ([string]::IsNullOrWhiteSpace($ContainerId)) {
                continue
            }

            $ImageId = docker inspect `
                $Entry.Name `
                --format "{{.Image}}" `
                2>$null

            $Status = docker inspect `
                $Entry.Name `
                --format "{{.State.Status}}" `
                2>$null

            $LiveContainers[$Entry.Logical] = [ordered]@{
                container = $Entry.Name
                container_id = ([string]$ContainerId).Trim()
                image_id = ([string]$ImageId).Trim()
                status = ([string]$Status).Trim()
            }

            Add-Line (
                "{0} CONTAINER_ID={1} IMAGE_ID={2} STATUS={3}" -f
                $Entry.Logical,
                ([string]$ContainerId).Trim(),
                ([string]$ImageId).Trim(),
                ([string]$Status).Trim()
            )

            if (
                ([string]$Status).Trim() -eq "running"
            ) {

                Pass "Live container is running: $($Entry.Name)"

            }
            else {

                Warn "Live container is not running: $($Entry.Name)"

            }

        }
        catch {
        }
    }

    if ($LiveContainers.Count -gt 0) {
        Pass "Live container/image identities were captured."
    }
    else {
        Not-Proven "Live container image consistency could not be established."
    }

    # ========================================================
    # [8] CONFIGURATION CONTRACT
    # ========================================================

    Section "[8] RELEASE CONFIGURATION CONTRACT"

    $ConfigFiles = @(
        ".env.production.example",
        "docker-compose.yml",
        "Dockerfile",
        ".dockerignore"
    )

    $ConfigContract = [ordered]@{}

    foreach ($RelativePath in $ConfigFiles) {

        $Path = Join-Path $Root $RelativePath

        if (Test-Path -LiteralPath $Path) {

            $Hash = Get-Hash $Path

            $ConfigContract[$RelativePath] = [ordered]@{
                sha256 = $Hash
            }

            Add-Line "$RelativePath SHA256=$Hash"

            Pass "Configuration contract fingerprint captured: $RelativePath"

        }
        else {

            $ConfigContract[$RelativePath] = $null

            Warn "Configuration contract file is absent: $RelativePath"

        }
    }

    # Extract only safe configuration metadata.
    # Values themselves are never written for secrets.

    $ProductionExampleText = Read-TextSafe (
        Join-Path $Root ".env.production.example"
    )

    $ConfigurationSignals = [ordered]@{
        docs_setting_present =
            (
                $ProductionExampleText -match '(?mi)^\s*ENABLE_DOCS\s*='
            )

        cors_setting_present =
            (
                $ProductionExampleText -match '(?mi)^\s*(CORS_ORIGINS|CORS_ALLOWED_ORIGINS)\s*='
            )

        runtime_db_role_present = (
            (
                [string]$ComposeText -match '(?i)aurix[_-]runtime'
            ) -or
            (
                [string]$ComposeText -match '(?i)DATABASE_URL\s*=\s*[^@\r\n]*aurix[_-]runtime'
            )
        )

        privileged_runtime_db_reference =
            (
                $ComposeText -match '(?im)DATABASE_URL=.*aurix[:@]'
            )

        production_environment_signal =
            (
                $ProductionExampleText -match '(?mi)^\s*ENVIRONMENT\s*='
            )
    }

    foreach ($Signal in $ConfigurationSignals.Keys) {

        Add-Line (
            "{0}={1}" -f
            $Signal,
            $ConfigurationSignals[$Signal]
        )

    }

    if ($ConfigurationSignals.runtime_db_role_present) {
        Pass "Configuration contract references aurix_runtime."
    }
    else {
        Fail "Configuration contract does not reference aurix_runtime."
    }

    if ($ConfigurationSignals.privileged_runtime_db_reference) {
        Fail "Configuration contract contains a privileged aurix DATABASE_URL reference."
    }
    else {
        Pass "No privileged aurix DATABASE_URL reference found."
    }

    # ========================================================
    # [9] RELEASE METADATA RECONCILIATION WITH LIVE API
    # ========================================================

    Section "[9] LIVE API RELEASE METADATA"

    $ApiMetadata = [ordered]@{}

    try {

        $Health = Invoke-RestMethod `
            -Uri "http://localhost:8000/api/v1/health" `
            -Method Get `
            -TimeoutSec 15 `
            -ErrorAction Stop

        $ApiJson = $Health | ConvertTo-Json -Depth 50

        Add-Line $ApiJson

        # Health metadata is returned under the response .data object.
        # Fall back to the top-level object for backward compatibility.

        $HealthData = $Health.data

        if ($null -eq $HealthData) {
            $HealthData = $Health
        }

        $ApiMetadata.environment =
            [string]$HealthData.environment

        $ApiMetadata.build_version =
            [string]$HealthData.build_version

        $ApiMetadata.schema_version =
            [string]$HealthData.schema_version

        $ApiMetadata.release_commit =
            [string]$HealthData.release_commit

        $ApiMetadata.status =
            [string]$HealthData.status

        $ApiMetadata.database =
            [string]$HealthData.database

        $ApiMetadata.redis =
            [string]$HealthData.redis
            [string]$Health.redis

        Add-Line "LIVE_ENVIRONMENT=$($ApiMetadata.environment)"
        Add-Line "LIVE_BUILD_VERSION=$($ApiMetadata.build_version)"
        Add-Line "LIVE_SCHEMA_VERSION=$($ApiMetadata.schema_version)"
        Add-Line "LIVE_RELEASE_COMMIT=$($ApiMetadata.release_commit)"

        Pass "Live API release metadata endpoint responded."

        if (
            $ApiMetadata.release_commit -match '^[0-9a-f]{40}$'
        ) {

            Pass "Live API reports an exact Git SHA."

            if (
                -not [string]::IsNullOrWhiteSpace($GitSha) -and
                $ApiMetadata.release_commit -eq $GitSha
            ) {

                Pass "Live API release commit matches current repository HEAD."

            }
            else {

                Fail "Live API release commit does not match repository HEAD."

            }

        }
        elseif (
            $ApiMetadata.release_commit -match '(?i)^HEAD$'
        ) {

            Fail "Live API still reports release_commit=HEAD."

        }
        else {

            Warn "Live API release commit is not a 40-character Git SHA."

        }

        if (
            $ApiMetadata.environment -match '(?i)^production$'
        ) {

            Pass "Live API environment is production."

        }
        else {

            Warn "Live API environment is not production."

        }

        if (
            -not [string]::IsNullOrWhiteSpace($BackendVersion) -and
            $ApiMetadata.build_version -eq $BackendVersion
        ) {

            Pass "Live API build version matches backend project version."

        }
        elseif (
            [string]::IsNullOrWhiteSpace($ApiMetadata.build_version)
        ) {

            Not-Proven "Live API did not provide build_version."

        }
        else {

            Warn "Live API build_version differs from the backend project version."

        }

        if (
            $ApiMetadata.database -match '(?i)healthy' -or
            $ApiMetadata.status -match '(?i)healthy'
        ) {

            Pass "Live API health reports an operational state."

        }

    }
    catch {

        Not-Proven "Live API release metadata could not be retrieved."

    }

    # ========================================================
    # [10] EXACT SOURCE TREE FINGERPRINT
    # ========================================================

    Section "[10] SOURCE TREE FINGERPRINT"

    $TrackedGitOutput = Get-GitOutput -Arguments @(
        "ls-files"
    )

    $TrackedFiles = @(
        ($TrackedGitOutput -split "`r?`n") |
        Where-Object {
            -not [string]::IsNullOrWhiteSpace($_)
        }
    )

    Add-Line "Tracked Git files: $($TrackedFiles.Count)"

    if ($TrackedFiles.Count -gt 0) {

        $TreeHasher = Join-Path `
            $env:TEMP `
            ("aurix_step11_tree_" +
                [guid]::NewGuid().ToString("N") +
                ".txt")

        try {

            $CanonicalTree = [System.Collections.Generic.List[string]]::new()

            foreach ($RelativePath in (
                $TrackedFiles |
                Sort-Object
            )) {

                $FullPath = Join-Path `
                    $Root `
                    $RelativePath

                if (-not (Test-Path -LiteralPath $FullPath)) {
                    continue
                }

                $Hash = Get-Hash $FullPath

                [void]$CanonicalTree.Add(
                    "$RelativePath`t$Hash"
                )

            }

            [System.IO.File]::WriteAllLines(
                $TreeHasher,
                $CanonicalTree,
                [System.Text.UTF8Encoding]::new($false)
            )

            $SourceTreeSha256 = Get-Hash $TreeHasher

            Add-Line "SOURCE_TREE_SHA256=$SourceTreeSha256"

            if (-not [string]::IsNullOrWhiteSpace($SourceTreeSha256)) {

                Pass "Deterministic tracked-source-tree fingerprint generated."

            }
            else {

                Fail "Source-tree fingerprint could not be generated."

            }

        }
        finally {

            Remove-Item `
                -LiteralPath $TreeHasher `
                -Force `
                -ErrorAction SilentlyContinue

        }

    }
    else {

        Fail "No tracked Git files were found."

        $SourceTreeSha256 = ""

    }

    # ========================================================
    # [11] RELEASE REPRODUCIBILITY CONDITIONS
    # ========================================================

    Section "[11] RELEASE REPRODUCIBILITY"

    $ReproducibilityReady = $true

    if (
        [string]::IsNullOrWhiteSpace($GitSha) -or
        $GitSha -notmatch '^[0-9a-f]{40}$'
    ) {

        $ReproducibilityReady = $false
        Fail "Release reproducibility lacks an exact Git SHA."

    }

    if ([string]::IsNullOrWhiteSpace($SourceTreeSha256)) {

        $ReproducibilityReady = $false
        Fail "Release reproducibility lacks a source-tree fingerprint."

    }

    if ($MigrationHead -and
        $MigrationHead -ne ""
    ) {

        Pass "Release manifest contains a single migration head."

    }
    else {

        $ReproducibilityReady = $false

    }

    if ($DependencyFingerprints.Count -gt 0) {

        Pass "At least one dependency fingerprint is captured."

    }
    else {

        Warn "No dependency lock fingerprint is available."

    }

    $MissingImageDigests = @(
        $ReleaseImages.GetEnumerator() |
        Where-Object {
            [string]::IsNullOrWhiteSpace(
                [string]$_.Value.digest
            )
        }
    )

    if ($ReleaseImages.Count -eq 0) {

        Warn "No Docker image identities were captured."

    }
    elseif ($MissingImageDigests.Count -eq 0) {

        Pass "All captured Docker service images have immutable digests."

    }
    else {

        Warn "One or more captured Docker images lack repository digests."

    }

    if ($GitStatus) {

        $ReproducibilityReady = $false

        Warn "Working tree contains changes; the release candidate is not based on a clean tree."

    }

    if ($ReproducibilityReady) {

        Pass "Core release reproducibility conditions are satisfied."

    }
    else {

        Warn "Release reproducibility conditions are not fully satisfied."

    }

    # ========================================================
    # [12] RELEASE MANIFEST GENERATION
    # ========================================================

    Section "[12] RELEASE MANIFEST"

    $ReleaseTimestamp = (
        Get-Date
    ).ToUniversalTime().ToString(
        "yyyy-MM-ddTHH:mm:ss.fffZ"
    )

    $ReleaseVersion = ""

    if (
        -not [string]::IsNullOrWhiteSpace($BackendVersion)
    ) {

        $ReleaseVersion = $BackendVersion

    }
    elseif (
        -not [string]::IsNullOrWhiteSpace($FrontendVersion)
    ) {

        $ReleaseVersion = $FrontendVersion

    }
    else {

        # Do not invent a semantic version.
        $ReleaseVersion = "UNVERSIONED"

    }

    $ManifestObject = [ordered]@{

        release = [ordered]@{

            release_version = $ReleaseVersion
            release_timestamp_utc = $ReleaseTimestamp

        }

        source = [ordered]@{

            git_sha = $GitSha
            git_short_sha = $GitShortSha
            git_branch = $GitBranch
            git_tag = $GitTag
            git_commit_date = $GitCommitDate
            working_tree_clean = [string]::IsNullOrWhiteSpace($GitStatus)
            source_tree_sha256 = $SourceTreeSha256

        }

        software = [ordered]@{

            backend_version = $BackendVersion
            frontend_version = $FrontendVersion

        }

        schema = [ordered]@{

            schema_version_numeric = $SchemaVersion
            migration_head = $MigrationHead

        }

        dependencies = $DependencyFingerprints

        docker = [ordered]@{

            services = $ReleaseImages

        }

        live_runtime = [ordered]@{

            containers = $LiveContainers
            api_metadata = $ApiMetadata

        }

        configuration = [ordered]@{

            files = $ConfigContract
            signals = $ConfigurationSignals

        }

        audit = [ordered]@{

            reproducibility_ready = $ReproducibilityReady

        }

    }

    $ManifestJson = (
        $ManifestObject |
        ConvertTo-Json -Depth 20
    )

    [System.IO.File]::WriteAllText(
        $Manifest,
        $ManifestJson,
        [System.Text.UTF8Encoding]::new($false)
    )

    Pass "Release manifest generated."

    # Stable latest manifest copy.
    try {

        [System.IO.File]::Copy(
            $Manifest,
            $LatestManifest,
            $true
        )

        Pass "Stable latest release manifest published."

    }
    catch {

        Warn "Stable latest release manifest could not be published."

    }

    # ========================================================
    # [13] MANIFEST SELF-HASH
    # ========================================================

    Section "[13] RELEASE MANIFEST INTEGRITY"

    $ManifestHash = Get-Hash $Manifest

    if (-not [string]::IsNullOrWhiteSpace($ManifestHash)) {

        Add-Line "MANIFEST_SHA256=$ManifestHash"

        Pass "Release manifest SHA-256 captured."

    }
    else {

        Fail "Release manifest SHA-256 could not be captured."

    }

    # ========================================================
    # [14] FINAL GATE
    # ========================================================

    Section "[14] STEP 11 FINAL GATE"

    Add-Line ""
    Add-Line "PASS COUNT       : $($Passes.Count)"
    Add-Line "WARNING COUNT    : $($Warnings.Count)"
    Add-Line "NOT PROVEN COUNT : $($NotProven.Count)"
    Add-Line "FAIL COUNT       : $($Failures.Count)"

    Add-Line ""

    if (
        $Failures.Count -eq 0 -and
        $NotProven.Count -eq 0 -and
        $ReproducibilityReady
    ) {

        Add-Line "RELEASE_CANDIDATE_FREEZE = PASS"
        Add-Line "STEP_11 = COMPLETE"

    }
    elseif (
        $Failures.Count -eq 0
    ) {

        Add-Line "RELEASE_CANDIDATE_FREEZE = PASS_WITH_UNPROVEN_BOUNDARIES"
        Add-Line "STEP_11 = COMPLETE_WITH_BOUNDARIES"

    }
    else {

        Add-Line "RELEASE_CANDIDATE_FREEZE = FAIL"
        Add-Line "STEP_11 = NOT_READY"

    }

    Add-Line ""
    Add-Line "RELEASE_VERSION=$ReleaseVersion"
    Add-Line "GIT_SHA=$GitSha"
    Add-Line "MIGRATION_HEAD=$MigrationHead"
    Add-Line "BACKEND_VERSION=$BackendVersion"
    Add-Line "FRONTEND_VERSION=$FrontendVersion"
    Add-Line "MANIFEST_SHA256=$ManifestHash"
    Add-Line ""
    Add-Line "No migrations were executed."
    Add-Line "No database records were inserted."
    Add-Line "No running containers were recreated."
    Add-Line "No source files outside AURIX_STEP11 were modified."

}
catch {

    $Message = $_.Exception.Message

    Add-Line "[FAIL] Fatal Step 11 audit exception: $Message"

    [void]$Failures.Add(
        "Fatal Step 11 audit exception: $Message"
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
# CONSOLE OUTPUT
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "AURIX STEP 11 MASTER - FINAL OUTPUT"
Write-Host "============================================================"
Write-Host "REPORT   : $Report"
Write-Host "MANIFEST : $Manifest"
Write-Host "LATEST   : $LatestReport"
Write-Host "LATEST MANIFEST : $LatestManifest"
Write-Host ""
Write-Host "PASS COUNT    : $($Passes.Count)"
Write-Host "WARNING COUNT : $($Warnings.Count)"
Write-Host "NOT PROVEN    : $($NotProven.Count)"
Write-Host "FAIL COUNT    : $($Failures.Count)"
Write-Host ""

if (
    $Failures.Count -eq 0 -and
    $NotProven.Count -eq 0 -and
    $ReproducibilityReady
) {

    Write-Host "RELEASE_CANDIDATE_FREEZE = PASS" -ForegroundColor Green
    Write-Host "STEP_11 = COMPLETE" -ForegroundColor Green

}
elseif ($Failures.Count -eq 0) {

    Write-Host "RELEASE_CANDIDATE_FREEZE = PASS_WITH_UNPROVEN_BOUNDARIES" -ForegroundColor Yellow
    Write-Host "STEP_11 = COMPLETE_WITH_BOUNDARIES" -ForegroundColor Yellow

}
else {

    Write-Host "RELEASE_CANDIDATE_FREEZE = FAIL" -ForegroundColor Red
    Write-Host "STEP_11 = NOT_READY" -ForegroundColor Red

}

Write-Host ""
Write-Host "============================================================"
Write-Host "STEP 11 MASTER COMPLETE"
Write-Host "============================================================"
