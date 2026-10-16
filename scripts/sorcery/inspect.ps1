# Sorcery job: read-only checks in ephemeral GitHub Actions runner.
$ErrorActionPreference = "Stop"
Write-Host "i Sorcery PowerShell: safe diagnostics"
Write-Host ("Platform: " + [System.Runtime.InteropServices.RuntimeInformation]::OSDescription)
Write-Host ("PowerShell: " + $PSVersionTable.PSVersion)
git rev-parse --verify HEAD
git status --porcelain=v1
python --version
