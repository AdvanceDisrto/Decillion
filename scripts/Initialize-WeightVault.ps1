[CmdletBinding()]
param(
    [string]$VaultPath = "E:\iDecillion\ModelVault",
    [UInt64]$QuotaBytes = 0,
    [UInt64]$ReserveBytes = 10737418240
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProjectFile = Join-Path $ProjectRoot "pyproject.toml"
if (-not (Test-Path -LiteralPath $ProjectFile -PathType Leaf)) {
    throw "Run this script from the cloned Decillion repository."
}

$VaultRoot = [System.IO.Path]::GetPathRoot($VaultPath)
if (-not $VaultRoot -or -not (Test-Path -LiteralPath $VaultRoot -PathType Container)) {
    throw "External destination drive is unavailable: $VaultRoot"
}

$VenvPath = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) { throw "Python virtual environment creation failed." }
}

& $Python -m pip install -e "${ProjectRoot}[models]"
if ($LASTEXITCODE -ne 0) { throw "Decillion model dependencies failed to install." }

$ModelCli = Join-Path $VenvPath "Scripts\decillion-models.exe"
& $ModelCli vault-init `
    --destination $VaultPath `
    --quota-bytes $QuotaBytes `
    --reserve-bytes $ReserveBytes
if ($LASTEXITCODE -ne 0) { throw "External weight vault initialization failed." }

& $ModelCli vault-status --destination $VaultPath
if ($LASTEXITCODE -ne 0) { throw "External weight vault status check failed." }

Write-Host "EXTERNAL_WEIGHT_VAULT_READY: $VaultPath" -ForegroundColor Green
