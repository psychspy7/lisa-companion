param(
 [string]$Python='python',
 [Parameter(Mandatory=$true)][string]$Godot,
 [Parameter(Mandatory=$true)][string]$Templates,
 [string]$Output='',
 [string]$InnoCompiler=''
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $Output) { $Output=Join-Path $PSScriptRoot 'dist' }
$env:LISA_GODOT=$Godot
& $Python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Lisa tests failed' }
$lisaBuildArgs=@('installer/build_godot.py','--godot',$Godot,'--templates',$Templates,'--output',$Output)
if ($InnoCompiler) { $lisaBuildArgs+=@('--compiler',$InnoCompiler) }
& $Python @lisaBuildArgs
if ($LASTEXITCODE -ne 0) { throw 'Lisa native build failed' }
Write-Output "Built native Godot app and LISA-Setup.exe in $Output"
