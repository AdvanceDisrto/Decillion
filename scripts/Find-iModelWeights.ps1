# i™ Model Weight Finder - non-destructive Windows/PowerShell evidence audit.
# Run locally; DO NOT commit checkpoints, API keys, or decrypted weight material.
param(
 [string[]]$Roots = @("$HOME\Desktop\iNNOVULiS-Matrix","E:\iDecillion\ModelVault","E:\iModels","E:\"),
 [string]$ReportDirectory = "$HOME\Desktop\iModel-Weight-Audit",
 [int]$MaximumFiles = 150000
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null
$wanted = @(".safetensors",".gguf",".pt",".pth",".ckpt",".onnx",".bin")
$results = [Collections.Generic.List[object]]::new()
$scanProblems = [Collections.Generic.List[string]]::new()
foreach($root in ($Roots | Select-Object -Unique)){
 if(-not (Test-Path -LiteralPath $root)){continue}
 $count=0
 Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction SilentlyContinue -ErrorVariable +listingErrors |
 Where-Object { $_.Extension.ToLowerInvariant() -in $wanted -or $_.Name -in @("model.safetensors.index.json","pytorch_model.bin.index.json","config.json","tokenizer.json","decillion-manifest.json") } |
 ForEach-Object {
  if($count -lt $MaximumFiles) {
    $count++
    $looksLikeWeight = $_.Extension.ToLowerInvariant() -in $wanted
    $results.Add([pscustomobject]@{
      Path=$_.FullName; Bytes=$_.Length
      Category= if($looksLikeWeight){"possible-weight-file"}else{"config-or-manifest"}
      ModifiedUTC=$_.LastWriteTimeUtc.ToString("o")
      SHA256= if($_.Length -le 268435456 -and $looksLikeWeight){(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}else{"not-computed-large-file"}
      CheckpointValidated=$false; Apache2LicenseValidated=$false
    })
  }
 }
}
$out=Join-Path $ReportDirectory "iModel-Weight-Inventory.json"
$results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "i™ Weight candidates recorded: $($results.Count)" -ForegroundColor Green
Write-Host "Report: $out"
Write-Host "Candidates are NOT verified trained checkpoints or Apache-2.0-licensed weights."
$results | Group-Object Category | Select-Object Name,Count | Format-Table -AutoSize
