param([Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference = 'Stop'
# Official Inno Setup 6.7.3, verified against its valid Pyrsys B.V. signature.
$lisaCompilerHash = '9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732'
$lisaCompilerUrl = 'https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe'
$lisaCompilerRoot = [IO.Path]::GetFullPath($Output)
New-Item -ItemType Directory -Force -Path $lisaCompilerRoot | Out-Null
$lisaCompilerDownload = Join-Path $lisaCompilerRoot 'innosetup-6.7.3.exe'
if (-not (Test-Path -LiteralPath $lisaCompilerDownload) -or
    (Get-FileHash -Algorithm SHA256 -LiteralPath $lisaCompilerDownload).Hash.ToLowerInvariant() -ne $lisaCompilerHash) {
    Invoke-WebRequest -Uri $lisaCompilerUrl -OutFile $lisaCompilerDownload
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $lisaCompilerDownload).Hash.ToLowerInvariant() -ne $lisaCompilerHash) {
    throw 'Official compiler download checksum did not match.'
}
$lisaCompilerSignature = Get-AuthenticodeSignature -LiteralPath $lisaCompilerDownload
if ($lisaCompilerSignature.Status -ne 'Valid') { throw 'Official compiler signature did not verify.' }
$lisaCompilerFolder = Join-Path $lisaCompilerRoot 'compiler'
$lisaCompilerProcess = Start-Process -FilePath $lisaCompilerDownload -ArgumentList @(
    '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', '/PORTABLE=1', '/CURRENTUSER',
    ('/DIR="' + $lisaCompilerFolder + '"')
) -WindowStyle Hidden -Wait -PassThru
if ($lisaCompilerProcess.ExitCode -ne 0) { throw 'Could not extract the portable compiler.' }
$env:LISA_ISCC = Join-Path $lisaCompilerFolder 'ISCC.exe'
if (-not (Test-Path -LiteralPath $env:LISA_ISCC)) { throw 'The compiler was not extracted.' }
Write-Output "Inno Setup compiler ready: $env:LISA_ISCC"
