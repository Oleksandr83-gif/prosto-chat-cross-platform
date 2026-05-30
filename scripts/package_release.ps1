param(
  [string]$OutputDir = "dist",
  [string]$ReleaseName = "prosto-chat-release"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$dist = Join-Path $root $OutputDir
$staging = Join-Path $dist $ReleaseName
$archive = Join-Path $dist "$ReleaseName.zip"

if (Test-Path $staging) {
  Remove-Item -LiteralPath $staging -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $staging | Out-Null

$excludeDirs = @(
  ".venv",
  "dist",
  ".git",
  "__pycache__",
  ".pytest_cache"
)

$excludeFiles = @(
  "*.pyc",
  "*.pyo",
  "*.db",
  ".env"
)

Get-ChildItem -LiteralPath $root -Force | ForEach-Object {
  if ($excludeDirs -contains $_.Name) {
    return
  }

  $destination = Join-Path $staging $_.Name
  if ($_.PSIsContainer) {
    robocopy $_.FullName $destination /E /XD $excludeDirs /XF $excludeFiles | Out-Null
    if ($LASTEXITCODE -gt 7) {
      throw "robocopy failed for $($_.FullName) with code $LASTEXITCODE"
    }
    $global:LASTEXITCODE = 0
  } else {
    $skip = $false
    foreach ($pattern in $excludeFiles) {
      if ($_.Name -like $pattern) {
        $skip = $true
        break
      }
    }
    if (-not $skip) {
      Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    }
  }
}

if (Test-Path $archive) {
  Remove-Item -LiteralPath $archive -Force
}

Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $archive -Force
Write-Host "Release archive created: $archive"

