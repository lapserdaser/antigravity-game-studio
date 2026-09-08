# Antigravity Game Studio Setup
# Run this script on any PC to deploy all rules and skills into Antigravity config
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$targetConfig = Join-Path $env:USERPROFILE ".gemini\config"
Write-Host "Target Antigravity config directory: $targetConfig" -ForegroundColor Cyan

if (-not (Test-Path $targetConfig)) {
    New-Item -ItemType Directory -Path $targetConfig -Force | Out-Null
}

# Copy rules
$destRules = Join-Path $targetConfig "rules"
New-Item -ItemType Directory -Path $destRules -Force | Out-Null
Copy-Item -Path "rules\*" -Destination $destRules -Recurse -Force
Write-Host "[OK] Rules updated in $destRules" -ForegroundColor Green

# Copy skills
$destSkills = Join-Path $targetConfig "skills"
New-Item -ItemType Directory -Path $destSkills -Force | Out-Null
Copy-Item -Path "skills\*" -Destination $destSkills -Recurse -Force
Write-Host "[OK] Skills updated in $destSkills" -ForegroundColor Green

# Deploy MCP config with resolved environment paths
$destMcp = Join-Path $targetConfig "mcp_config.json"
if (-not (Test-Path $destMcp)) {
    if (Test-Path "mcp\mcp_config.json") {
        $mcpRaw = Get-Content "mcp\mcp_config.json" -Raw -Encoding UTF8
        $mcpResolved = $mcpRaw.Replace("%APPDATA%", $env:APPDATA).Replace("%LOCALAPPDATA%", $env:LOCALAPPDATA)
        [System.IO.File]::WriteAllText($destMcp, $mcpResolved, [System.Text.Encoding]::UTF8)
        Write-Host "[OK] Configured and copied mcp_config.json to $destMcp" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Existing mcp_config.json preserved. See mcp/mcp_config.example.json for template." -ForegroundColor Yellow
}

Write-Host "`nAll agents, rules, and skills successfully installed into Antigravity!" -ForegroundColor Green
