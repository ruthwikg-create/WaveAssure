# WaveAssure source publication helper (Windows PowerShell 5.1+)
# Creates a PRIVATE GitHub repo owned by ruthwikg-create, or pushes to that
# existing PRIVATE repo. Does not push healthcare data or local model files.
# Requires Git and GitHub CLI ('gh') with a signed-in GitHub user.
param(
    [string]$Repository = 'ruthwikg-create/WaveAssure',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($Repository -cne 'ruthwikg-create/WaveAssure') {
    throw 'Safety guard: this script only publishes to ruthwikg-create/WaveAssure.'
}
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

$forbidden = @(
    '(^|/)\.env($|\.)',
    '(?i)\.(dat|hea|atr|sqlite|sqlite3|db|joblib|pkl|pickle|npz|parquet|pem|key|p12|pfx)$',
    '(?i)(^|/)(models|benchmark-results|reports/private|release-staging|\.venv)(/|$)',
    '(?i)(^|/)(id_rsa|id_ed25519|credentials|secrets)(\.|$)'
)

# Check ALL files, not just staged files, when no git repository exists.
$allFiles = @(Get-ChildItem -Path $root -Recurse -File -Force | Where-Object {
    $_.FullName -notmatch '[\\/](\.git|\.venv|__pycache__|\.pytest_cache)[\\/]'
} | ForEach-Object { $_.FullName.Substring($root.Length+1).Replace('\','/') })
$unsafe = @($allFiles | Where-Object {
    $relative = $_
    @($forbidden | Where-Object { $relative -match $_ }).Count -gt 0
})
if ($unsafe.Count -gt 0) {
    Write-Host 'Refusing to publish: remove or relocate these private/data artifacts:' -ForegroundColor Red
    $unsafe | ForEach-Object { Write-Host "  $_" }
    throw 'Unsafe file(s) present in project tree.'
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git not installed. Install with: winget install --id Git.Git -e'
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI not installed. Install with: winget install --id GitHub.cli -e'
}

& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Sign into GitHub first using: gh auth login' }

# Check that GitHub CLI is authenticated to the intended owner account.
$login = (& gh api user --jq '.login' | Select-Object -First 1).Trim()
if ($LASTEXITCODE -ne 0 -or $login -cne 'ruthwikg-create') {
    throw "Authenticated GitHub login is '$login', not 'ruthwikg-create'. Refusing to publish."
}

$repoStatus = & gh repo view $Repository --json isPrivate --jq '.isPrivate' 2>$null
$exists = ($LASTEXITCODE -eq 0)
if ($exists -and $repoStatus.Trim() -ne 'true') {
    throw 'Repository already exists but is PUBLIC. Refusing to push; use a PRIVATE repository.'
}

if ($CheckOnly) {
    Write-Host "Checks passed. Repository exists: $exists; destination: $Repository" -ForegroundColor Green
    Write-Host 'No files pushed. Remove -CheckOnly to publish.'
    exit 0
}

# Refuse to use an enclosing unrelated git repository.
if (-not (Test-Path (Join-Path $root '.git'))) {
    $enclosing = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $enclosing) {
        throw "Project resides inside another Git repository: $enclosing. Use an independent folder."
    }
    & git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'Unable to initialize Git repository.' }
}

$remote = & git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $remote) {
    $expectedUrls = @("https://github.com/$Repository", "https://github.com/$Repository.git", "git@github.com:$Repository.git")
    if ($expectedUrls -cnotcontains $remote.Trim()) {
        throw "origin remote points to unexpected repository: $remote"
    }
}

& git add -A
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
$staged = @(& git diff --cached --name-only)
$unsafeStaged = @($staged | Where-Object {
    $relative = $_
    @($forbidden | Where-Object { $relative -match $_ }).Count -gt 0
})
if ($unsafeStaged.Count -gt 0) {
    $unsafeStaged | ForEach-Object { Write-Host "Rejected staged file: $_" -ForegroundColor Red }
    throw 'Refusing to commit protected file types.'
}
if ($staged.Count -eq 0 -and -not $exists) {
    throw 'Nothing staged in new repository; refusing to create an empty repository.'
}
if ($staged.Count -gt 0) {
    & git commit -m 'WaveAssure v0.9.0: research-only safety corrections'
    if ($LASTEXITCODE -ne 0) {
        throw 'Commit failed. Configure your Git user.name and user.email and retry.'
    }
}

if (-not $exists) {
    & gh repo create $Repository --private --source . --remote origin --push --description 'Research-only biomedical signal integrity and VT alarm investigation workbench'
    if ($LASTEXITCODE -ne 0) { throw 'GitHub repo creation or push failed. No clinical approval implied.' }
} else {
    if (-not $remote) {
        & git remote add origin "https://github.com/$Repository.git"
        if ($LASTEXITCODE -ne 0) { throw 'Could not configure origin remote.' }
    }
    & git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw 'Git push failed. No force push was attempted.' }
}
Write-Host "Source published to https://github.com/$Repository" -ForegroundColor Green
Write-Host 'RESEARCH ONLY. This is NOT clinical certification or authorization.'
