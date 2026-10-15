# Only isolated CI runner. Never run this installer against the owner's machine.
$ErrorActionPreference = 'Stop'
$url = 'https://github.com/browseros-ai/BrowserOS/releases/download/browserclaw/v0.51.1.2/BrowserOS_neo_v0.51.1.2_x64_installer.exe'
$expected = '7f3734afd6dbeb237023caab8028641a1c94868d5a244bfcfe95530cb810b191'
$installer = Join-Path $env:TEMP 'BrowserOS_neo_pinned.exe'
Invoke-WebRequest -Uri $url -OutFile $installer
if ((Get-FileHash $installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'BrowserOS installer hash mismatch' }
$env:CLAW_ANALYTICS_ENABLED = 'false'
$process = Start-Process -FilePath $installer -ArgumentList '--silent', '--do-not-launch-chrome' -Wait -PassThru
Write-Output "Pinned installer exit code: $($process.ExitCode)"
$roots = @($env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)}) | Where-Object { $_ -and (Test-Path $_) }
$candidates = foreach ($root in $roots) { Get-ChildItem $root -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'BrowserOS|BrowserClaw' } | ForEach-Object { Get-ChildItem $_.FullName -Filter '*.exe' -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(browseros|browserclaw|chrome)\.exe$' } } }
$chosen = @($candidates | Sort-Object FullName -Unique)
if ($chosen.Count -ne 1) { $chosen | ForEach-Object { Write-Output $_.FullName }; throw 'Pinned BrowserOS executable is missing or ambiguous' }
$env:BROWSEROS_EXE = $chosen[0].FullName
$version = $chosen[0].VersionInfo.ProductVersion
Write-Output "Installed BrowserOS version: $version"
# Chromium product version differs from BrowserOS release number. Installer exact SHA pin is authoritative; preserve this version evidence.
$env:PYTHONPATH = (Resolve-Path '../src').Path
python browseros-native-smoke.py
if ($LASTEXITCODE -ne 0) { throw 'Actual BrowserOS Windows integration failed' }
