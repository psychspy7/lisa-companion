param([string]$Python = 'python', [string]$Output = '', [string]$InnoCompiler = '')
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
    if ($LASTEXITCODE -ne 0) { throw 'Portable build failed' }
    & $Python -m PyInstaller --noconfirm --clean --distpath $Output lisa-installed.spec
} finally {
    $env:PATH = $lisaOriginalPath
}
if ($LASTEXITCODE -ne 0) { throw 'Installed app build failed' }
$lisaInstallerArgs = @('installer/build_setup.py', $Output)
if ($InnoCompiler) { $lisaInstallerArgs += @('--compiler', $InnoCompiler) }
& $Python @lisaInstallerArgs
if ($LASTEXITCODE -ne 0) { throw 'Installer build failed' }
Write-Output "Built LISA-Setup.exe and portable LISA.exe in $Output"
