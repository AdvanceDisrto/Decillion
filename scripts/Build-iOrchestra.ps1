# i™ Orchestra one-play: local OCI build + bound localhost test.
# Run from the Decillion repository root. Requires Docker Desktop installed/running.
# Creates no public DNS, OS installers, cloud charges, or carrier/mesh connections.
param(
  [string]$Tag = 'i-telecom-orchestra:local',
  [int]$HostPort = 18880
)
$ErrorActionPreference = 'Stop'
if ($HostPort -lt 1024 -or $HostPort -gt 65535) { throw 'Use an unprivileged TCP port 1024..65535' }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI is not installed' }
docker info | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Docker daemon is unavailable' }
$repo = (git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Run in a clone of Decillion' }
Push-Location $repo
try {
  docker build -f 'i-api/Dockerfile.orchestra' -t $Tag .
  if ($LASTEXITCODE -ne 0) { throw 'Orchestra image build failed' }
  $name = 'i-telecom-orchestra-local'
  $existing = docker ps -a --filter "name=^/$name$" --format '{{.Names}}'
  if ($existing -eq $name) { throw "Existing container $name found. Refusing to replace or delete it." }
  docker run -d --name $name -p "127.0.0.1:${HostPort}:8080" $Tag
  if ($LASTEXITCODE -ne 0) { throw 'Container start failed' }
  $ready = $false
  for ($i=0; $i -lt 25; $i++) {
    Start-Sleep -Seconds 1
    try {
      $h = Invoke-RestMethod -TimeoutSec 3 -Uri "http://127.0.0.1:$HostPort/health"
      if ($h.status -eq 'ok') { $ready = $true; break }
    } catch {}
  }
  if (-not $ready) { throw 'Local API did not pass health check; see docker logs i-telecom-orchestra-local' }
  $cap = Invoke-RestMethod -TimeoutSec 5 -Uri "http://127.0.0.1:$HostPort/v1/orchestra/capabilities"
  if ($cap.physical_network_orchestration -ne $false) { throw 'Unsafe real carrier status asserted unexpectedly' }
  $payload = @{ nodes=32; jobs=10000; dropout_fraction=0.5; seed=42 } | ConvertTo-Json
  $result = Invoke-RestMethod -Method POST -TimeoutSec 30 -Uri "http://127.0.0.1:$HostPort/v1/orchestra/simulate" -ContentType 'application/json' -Body $payload
  if ($result.metrics.completed_in_memory -ne 10000 -or $result.metrics.dropped_nodes -ne 16) { throw 'Orchestration mock acceptance failed' }
  Write-Host 'i™ ORCHESTRA PASS: local API healthy; simulated 50% node dropout, 10000 work units retained.' -ForegroundColor Green
  Write-Host "Local API: http://127.0.0.1:$HostPort"
  Write-Host "Container: $name (local host only)"
  Write-Host 'Reminder: no network carrier activated and no signed certificate issued.'
} finally { Pop-Location }
