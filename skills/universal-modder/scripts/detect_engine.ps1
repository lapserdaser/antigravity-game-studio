param (
    [Parameter(Mandatory=$true)]
    [string]$GamePath
)

if (-not (Test-Path -Path $GamePath)) {
    Write-Error "Game path does not exist: $GamePath"
    exit 1
}

$result = [PSCustomObject]@{
    Engine       = "Unknown"
    Architecture = "Unknown"
    Framework    = "Unknown"
    MainExe      = $null
    Evidence     = @()
}

# Scan executables
$exes = Get-ChildItem -Path $GamePath -Filter "*.exe" -File -Recurse -Depth 2 | Where-Object { $_.Name -notmatch "unins|crash|reporter|launcher|update" }
if ($exes.Count -gt 0) {
    $result.MainExe = $exes[0].FullName
}

# Check Unity (Mono vs IL2CPP)
$unityPlayer = Get-ChildItem -Path $GamePath -Filter "UnityPlayer.dll" -File -Recurse -Depth 2
if ($unityPlayer) {
    $result.Evidence += "Found UnityPlayer.dll"
    $il2cpp = Get-ChildItem -Path $GamePath -Filter "GameAssembly.dll" -File -Recurse -Depth 2
    if ($il2cpp) {
        $result.Engine = "Unity (IL2CPP)"
        $result.Framework = "BepInEx 6.x (IL2CPP) / MelonLoader"
    } else {
        $result.Engine = "Unity (Mono)"
        $result.Framework = "BepInEx 5.x / Harmony"
    }
}

# Check Unreal Engine
$unrealEngine = Get-ChildItem -Path $GamePath -Directory -Filter "Engine" -Recurse -Depth 2
$pakFiles = Get-ChildItem -Path $GamePath -Filter "*.pak" -File -Recurse -Depth 3
if ($unrealEngine -or $pakFiles) {
    $result.Engine = "Unreal Engine 4/5"
    $result.Framework = "UE4SS (Unreal Engine Scripting System)"
    if ($unrealEngine) { $result.Evidence += "Found Engine directory" }
    if ($pakFiles) { $result.Evidence += "Found .pak files" }
}

# Check Bethesda Creation Engine
$bethesdaFiles = Get-ChildItem -Path $GamePath -Include "*.esm", "*.ba2", "*.bsa" -File -Recurse -Depth 2
if ($bethesdaFiles) {
    $result.Engine = "Bethesda Creation Engine"
    $result.Framework = "SKSE / F4SE / Papyrus"
    $result.Evidence += "Found Bethesda archives (.esm/.ba2)"
}

# Check Godot
$godotPck = Get-ChildItem -Path $GamePath -Filter "*.pck" -File -Recurse -Depth 2
if ($godotPck) {
    $result.Engine = "Godot Engine"
    $result.Framework = "GDRE Tools / PCK Explorer / GDExtension"
    $result.Evidence += "Found Godot .pck file"
}

# Check Source Engine
$sourceBin = Get-ChildItem -Path $GamePath -Filter "engine.dll" -File -Recurse -Depth 3
if ($sourceBin) {
    $result.Engine = "Source Engine"
    $result.Framework = "Metamod / SourceHook / VScript"
    $result.Evidence += "Found Source engine.dll"
}

# Check RPG Maker MV/MZ
$rpgMakerPkg = Get-ChildItem -Path $GamePath -Filter "package.json" -File -Recurse -Depth 2
if ($rpgMakerPkg) {
    $content = Get-Content $rpgMakerPkg[0].FullName -Raw
    if ($content -match "RPG Maker|nwjs") {
        $result.Engine = "RPG Maker (MV/MZ)"
        $result.Framework = "JS Plugin Architecture"
        $result.Evidence += "Found RPG Maker package.json"
    }
}

# Check GameMaker
$gameMakerData = Get-ChildItem -Path $GamePath -Filter "data.win" -File -Recurse -Depth 2
if ($gameMakerData) {
    $result.Engine = "GameMaker"
    $result.Framework = "UndertaleModTool CLI"
    $result.Evidence += "Found data.win"
}

# Determine architecture of main exe if found
if ($result.MainExe -and (Test-Path $result.MainExe)) {
    try {
        $bytes = [System.IO.File]::ReadAllBytes($result.MainExe)
        # PE header offset is at 0x3C
        $peOffset = [System.BitConverter]::ToInt32($bytes, 0x3C)
        # Machine type is at peOffset + 4
        $machine = [System.BitConverter]::ToUInt16($bytes, $peOffset + 4)
        if ($machine -eq 0x8664) {
            $result.Architecture = "x64"
        } elseif ($machine -eq 0x014c) {
            $result.Architecture = "x86 (32-bit)"
        }
    } catch {
        $result.Architecture = "Could not parse PE"
    }
}

$result | ConvertTo-Json -Depth 3
