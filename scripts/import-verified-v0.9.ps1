# WaveAssure v0.9.0 source-import helper (PowerShell 5.1+)
# Execute locally on a computer that holds the GitHub-ready ZIP.
# Does not accept model or patient-data directories.
param(
  [Parameter(Mandatory=$true)][string]$ZipPath,
  [switch]$AllowPublic
)
$ErrorActionPreference = 'Stop'
$repo = 'ruthwikg-create/WaveAssure'
$expectedSha = '30636e75e6dbe57e34a9459e9bf34b8b90b16d1aaf070c9614f79ddbf399b137'
foreach ($command in @('git','gh')) {
  if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
    throw "$command is not installed."
  }
}
$src = (Resolve-Path $ZipPath).Path
$sha = (Get-FileHash $src -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sha -ne $expectedSha) { throw "ZIP SHA-256 did not match the verified v0.9.0 source bundle. Do not upload it." }
& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Run gh auth login first.' }
$login = (& gh api user --jq '.login' | Select-Object -First 1).Trim()
if ($LASTEXITCODE -ne 0 -or $login -ne 'ruthwikg-create') { throw 'Wrong GitHub login.' }
$visibility = (& gh repo view $repo --json isPrivate --jq '.isPrivate' | Select-Object -First 1).Trim()
if ($LASTEXITCODE -ne 0) { throw 'WaveAssure repo not accessible.' }
if ($visibility -ne 'true' -and -not $AllowPublic) {
  throw 'Repository is PUBLIC. Change it to private, or deliberately rerun using -AllowPublic for source-only publication.'
}
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('waveassure-publish-' + [guid]::NewGuid().ToString('N'))
$expanded = Join-Path $tempRoot 'expanded'
$clone = Join-Path $tempRoot 'checkout'
New-Item -ItemType Directory -Force -Path $expanded | Out-Null
try {
  Expand-Archive -LiteralPath $src -DestinationPath $expanded -Force
  $project = Join-Path $expanded 'WaveAssure'
  if (-not (Test-Path (Join-Path $project 'waveassure/api.py')) -or
      -not (Test-Path (Join-Path $project 'tests/test_safety_hardening09.py'))) {
    throw 'Invalid WaveAssure source ZIP layout.'
  }
  $forbidden = '(?i)(^|/)(models|benchmark-results|release-staging|\.venv|__pycache__|\.git)(/|$)|(^|/)\.env($|\.)|\.(dat|hea|atr|db|sqlite|sqlite3|pkl|pickle|joblib|npz|parquet|pem|key|p12|pfx)$'
  $files = @(Get-ChildItem $project -Recurse -File -Force | ForEach-Object {
    $relative = $_.FullName.Substring($project.Length+1).Replace('\','/')
    if ($relative -match $forbidden) { throw "Refusing unsafe file: $relative" }
    [PSCustomObject]@{ Source=$_.FullName; Relative=$relative }
  })
  if ($files.Count -lt 85) { throw "Unexpectedly few source files: $($files.Count)." }
  & gh repo clone $repo $clone
  if ($LASTEXITCODE -ne 0) { throw 'GitHub clone failed.' }
  foreach ($f in $files) {
    $target = Join-Path $clone ($f.Relative.Replace('/','\'))
    $parent = Split-Path $target -Parent
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $f.Source -Destination $target -Force
  }
  Push-Location $clone
  try {
    & git add -A
    if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
    $staged = @(& git diff --cached --name-only)
    foreach($p in $staged) { if($p -match $forbidden) { throw "Unsafe staged file: $p" } }
    if($staged.Count -eq 0){ Write-Host 'Repository already matches the source.'; exit 0 }
    $identity = & gh api user --jq '.id'
    & git -c "user.name=$login" -c "user.email=$identity+$login@users.noreply.github.com" commit -m 'Import WaveAssure v0.9.0 research source and tests'
    if ($LASTEXITCODE -ne 0) { throw 'Git commit failed' }
    & git push origin HEAD:main
    if ($LASTEXITCODE -ne 0) { throw 'Git push failed. No force push attempted.' }
    Write-Host "Uploaded $($staged.Count) changed paths to https://github.com/$repo"
    Write-Host 'RESEARCH ONLY: no clinical authorization.'
  } finally { Pop-Location }
} finally {
  if (Test-Path $tempRoot) { Remove-Item $tempRoot -Recurse -Force }
}
