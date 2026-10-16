# i™-Silo-1 non-destructive acceptance runner, Windows PowerShell 7 recommended.
# Runs USER-SPACE tests only. Never loads kernel drivers or maps MMIO.
param([switch]$IncludeOptionalTools)
$ErrorActionPreference="Stop"
$repo = (git rev-parse --show-toplevel).Trim()
if($LASTEXITCODE -ne 0){throw "Run inside Decillion clone"}
Set-Location $repo
$python=Get-Command py -ErrorAction SilentlyContinue
if(-not $python){throw "Python launcher 'py' is required"}
if(-not (Test-Path ".vpu-test-venv\Scripts\python.exe")){
    py -3 -m venv .vpu-test-venv
    if($LASTEXITCODE -ne 0){throw "Virtual environment creation failed"}
}
$pyexe=Join-Path $repo ".vpu-test-venv\Scripts\python.exe"
& $pyexe -m pip install -r i-api\requirements.txt
if($LASTEXITCODE -ne 0){throw "Dependencies failed to install"}
Push-Location i-api
try {
    & $pyexe -m unittest -v test_vpu_lab.py
    if($LASTEXITCODE -ne 0){throw "iCalcula Python test failed"}
} finally {Pop-Location}
if($IncludeOptionalTools){
    & $pyexe -m pip install 'grpcio>=1.67,<1.81'
    if($LASTEXITCODE -ne 0){throw "grpc install failed"}
    Push-Location i-api
    try {
        & $pyexe vpu_grpc_benchmark.py
        if($LASTEXITCODE -ne 0){throw "gRPC IPC benchmark failed"}
    } finally {Pop-Location}
    if(Get-Command go -ErrorAction SilentlyContinue){
       Push-Location edge\continuity
       try{go test -v ./...;if($LASTEXITCODE -ne 0){throw "Go test failed"}}finally{Pop-Location}
    }else{Write-Warning "Go not installed: skipping local queue tests"}
    if(Get-Command iverilog -ErrorAction SilentlyContinue){
      $out=Join-Path $env:TEMP "i-icalcula-tb.vvp"
      & iverilog -g2012 -Wall -s tb -o $out silicon/icalcula/im_icalcula_decoder.v silicon/icalcula/tb_icalcula_decoder.v
      if($LASTEXITCODE -ne 0){throw "HDL compile failed"}
      & vvp $out
      if($LASTEXITCODE -ne 0){throw "HDL simulation failed"}
    }else{Write-Warning "Icarus Verilog not installed: use GitHub CI or WSL to test HDL"}
}
Write-Host "i™ VPU LAB TESTS PASS. This is not a physical silicon certification." -ForegroundColor Green
