# Sentient-Grid Backend Launcher for PowerShell
# Runs the streaming backend as a background job or new window

param(
    [switch]$Background,
    [switch]$MQTT,
    [switch]$Faulty,
    [int]$Seed = 0,
    [string]$KafkaServers,
    [string]$LogFile = "sentient_grid_backend.log"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
Set-Location $ScriptDir

# Build arguments
$args = @("stream_backend.py")

if ($MQTT) {
    $args += "--mqtt"
}

if ($Faulty) {
    $args += "--faulty"
}

if ($Seed -gt 0) {
    $args += "--seed", $Seed
}

if ($KafkaServers) {
    $args += "--kafka-servers", $KafkaServers
}

$args += "--log-file", $LogFile

Write-Host "Starting Sentient-Grid Backend..."
Write-Host "Arguments: $($args -join ' ')"
Write-Host "Log file: $LogFile"
Write-Host ""

if ($Background) {
    # Start as a background job
    Write-Host "Starting in background mode (PowerShell Job)..."
    $job = Start-Job -ScriptBlock { 
        Set-Location $using:ScriptDir
        python @using:args
    }
    Write-Host "Job ID: $($job.Id)"
    Write-Host ""
    Write-Host "To monitor: Get-Job -Id $($job.Id) | Receive-Job -Wait"
    Write-Host "To stop: Stop-Job -Id $($job.Id)"
} else {
    # Start in new window
    Write-Host "Starting in new window..."
    Start-Process python -ArgumentList $args -NoNewWindow
    Write-Host "Backend process started."
    Write-Host "Monitor progress with: Get-Content $LogFile -Wait"
}
