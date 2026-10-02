param([string]$Python = 'python', [string]$Output = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $Output) { $Output = Join-Path $PSScriptRoot 'dist' }
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed --name LISA --icon assets/lisa.ico --add-data 'assets;assets' --add-data 'version.json;.' --collect-all sounddevice --distpath $Output app.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$lisaHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Output 'LISA.exe')).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Output 'SHA256SUMS.txt'), "$lisaHash  LISA.exe`n", [Text.UTF8Encoding]::new($false))
Write-Output "Built LISA.exe in $Output"
