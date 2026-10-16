# i™ iMobile local container compile / readiness / @username blackout smoke.
# Requires Git, Docker Desktop, cloned Decillion. Safe: does not replace existing containers.
param([string]$ContainerName="i-mobile-local",[int]$Port=18881)
$ErrorActionPreference="Stop"
if($Port -lt 1024 -or $Port -gt 65535){throw "Port outside 1024-65535"}
$root=(git rev-parse --show-toplevel).Trim()
if($LASTEXITCODE -ne 0){throw "Run from a Decillion repository"}
Set-Location $root
docker info | Out-Null
if($LASTEXITCODE -ne 0){throw "Docker service unavailable"}
$existing=docker ps -a --filter "name=^/$ContainerName$" --format "{{.Names}}"
if($existing -eq $ContainerName){throw "Existing container preserved: $ContainerName. Choose a different -ContainerName or stop/remove it manually."}
docker build -f i-api/Dockerfile.orchestra -t i-mobile-gateway:local .
if($LASTEXITCODE -ne 0){throw "Docker image build failed"}
$cid=(docker run -d --name $ContainerName -p "127.0.0.1:${Port}:8080" i-mobile-gateway:local).Trim()
if($LASTEXITCODE -ne 0){throw "Container launch failed"}
$healthy=$false
for($i=0;$i -lt 35;$i++){
  Start-Sleep -Seconds 1
  try {
    $response=Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 3
    if($response.status -eq "ok"){$healthy=$true;break}
  } catch {}
}
if(-not $healthy){docker logs $cid;throw "Health check failed"}
$body=@{from_handle="@sender";to_handle="@buddy";payload="Test only";total_nodes=12;blackout_fraction=0.5} | ConvertTo-Json
$result=Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/imobile/simulate" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 10
if($result.nodes_offline -ne 6 -or $result.status -ne "SIMULATED_NOT_TRANSMITTED" -or $result.packet.actually_delivered){throw "Network boundary test FAIL"}
$dir=Join-Path $HOME "Desktop\iMobile-Test-Evidence"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$dest=Join-Path $dir "i-mobile-offgrid-rehearsal.json"
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $dest -Encoding utf8
Write-Host "iMobile PASS: container HTTP serving, 50% outage test, no real packet delivery." -ForegroundColor Green
Write-Host "API: http://127.0.0.1:$Port | Evidence: $dest"
Write-Host "No native Android/iOS installers, SIM bypass or carrier integration is claimed."
