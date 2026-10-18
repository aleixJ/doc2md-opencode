<#
.SYNOPSIS
  Copy-only installer for the doc2md-opencode skill and command.

.DESCRIPTION
  Copies .opencode/skills/doc-to-md and .opencode/commands/doc2md.md into a
  project's .opencode directory or into the global OpenCode config directory.
  It never accesses the network and never modifies files outside the target.

.PARAMETER Project
  Target project directory (default: current directory).

.PARAMETER Global
  Install into ~/.config/opencode instead of a project.

.EXAMPLE
  ./install.ps1 -Project "C:\dev\my-app"

.EXAMPLE
  ./install.ps1 -Global
#>
[CmdletBinding()]
param(
    [string]$Project = ".",
    [switch]$Global
)

$ErrorActionPreference = "Stop"

$SourceRoot = Join-Path $PSScriptRoot ".opencode"
if (-not (Test-Path -LiteralPath $SourceRoot)) {
    Write-Error "Cannot find source directory: $SourceRoot"
    exit 1
}

if ($Global) {
    $DestRoot = Join-Path $env:USERPROFILE ".config\opencode"
}
else {
    $ResolvedProject = (Resolve-Path -LiteralPath $Project).Path
    $DestRoot = Join-Path $ResolvedProject ".opencode"
}

New-Item -ItemType Directory -Force -Path (Join-Path $DestRoot "skills") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DestRoot "commands") | Out-Null

Copy-Item -Path (Join-Path $SourceRoot "skills\*") -Destination (Join-Path $DestRoot "skills") -Recurse -Force
Copy-Item -Path (Join-Path $SourceRoot "commands\*") -Destination (Join-Path $DestRoot "commands") -Recurse -Force

# Never ship Python bytecode caches.
Get-ChildItem -Path $DestRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Installed doc2md-opencode into: $DestRoot"

# Probe by *execution*, not existence: the Microsoft Store `python3` alias is
# an executable that fails at runtime, so `Get-Command` alone is not enough.
$Python = $null
foreach ($Candidate in @("python3", "python", "py -3")) {
    $null = cmd /c "$Candidate --version 2>nul"
    if ($LASTEXITCODE -eq 0) { $Python = $Candidate; break }
}

if ($Python) {
    Write-Host "Detected Python launcher: $Python"
    $null = cmd /c "$Python -c `"import pymupdf`" 2>nul"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "PyMuPDF is not installed. Run:  $Python -m pip install pymupdf"
    }
}
else {
    Write-Warning "No working Python launcher found. Install Python 3.8+ and PyMuPDF."
}
