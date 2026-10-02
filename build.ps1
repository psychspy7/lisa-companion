param([string]$Python = 'python', [string]$Output = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $Output) { $Output = Join-Path $PSScriptRoot 'dist' }
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
$lisaOriginalPath = $env:PATH
try {
    # External document runtimes can expose an incompatible ICU DLL with the same name as Windows ICU.
    $env:PATH = (($lisaOriginalPath -split ';') | Where-Object { $_ -notmatch '[\\/]dependencies[\\/]native[\\/]' }) -join ';'
    & $Python -m PyInstaller --noconfirm --clean --distpath $Output lisa.spec
} finally {
    $env:PATH = $lisaOriginalPath
}
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$lisaHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Output 'LISA.exe')).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $Output 'SHA256SUMS.txt'), "$lisaHash  LISA.exe`n", [Text.UTF8Encoding]::new($false))
Write-Output "Built LISA.exe in $Output"
