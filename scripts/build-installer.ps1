#Requires -Version 5.1
<#
.SYNOPSIS
    Repackage the official smartmontools Windows installer with this repo's branding.

.DESCRIPTION
    Route A: no compiler required. Extracts the official setup.exe, rebuilds the
    32/64-bit input trees the way installer.nsi expects, applies patches/*.patch
    to a pristine source tree, then recompiles the installer with makensis.

    The binaries inside stay the official ones - only display strings change.

.PARAMETER OfficialSetup
    Path to the official smartmontools-*.win32-setup.exe.

.PARAMETER SourceTree
    Path to a pristine upstream source tree (RELEASE_7_5), used for installer.nsi.

.PARAMETER NsisDir
    NSIS directory containing Bin\makensis.exe (portable copy is fine).

.PARAMETER OutFile
    Output installer path.

.PARAMETER Version
    Four-part version written into the VERSIONINFO resource, e.g. 7.5.0.5714.

.PARAMETER VerString
    Free-form version banner, e.g. "7.5 2025-04-30 r5714".

.PARAMETER Year
    Two-digit year for the copyright line, e.g. 25.

.EXAMPLE
    .\build-installer.ps1 -OfficialSetup C:\Downloads\smartmontools-7.5.win32-setup.exe `
        -SourceTree C:\src\smartmontools -NsisDir C:\nsis `
        -OutFile .\smartmontools-develop-win32-setup.exe
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $OfficialSetup,
    [Parameter(Mandatory = $true)] [string] $SourceTree,
    [Parameter(Mandatory = $true)] [string] $NsisDir,
    [Parameter(Mandatory = $true)] [string] $OutFile,
    [string] $Version = '7.5.0.5714',
    [string] $VerString = '7.5 2025-04-30 r5714',
    [string] $Year = '25'
)

$ErrorActionPreference = 'Stop'

function Find-SevenZip {
    foreach ($p in @('C:\Program Files\7-Zip\7z.exe', 'C:\Program Files (x86)\7-Zip\7z.exe')) {
        if (Test-Path $p) { return $p }
    }
    $cmd = Get-Command 7z -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    throw '7-Zip not found (7z.exe).'
}

$sevenZip = Find-SevenZip
$makensis = Join-Path $NsisDir 'Bin\makensis.exe'
if (-not (Test-Path $makensis)) { $makensis = Join-Path $NsisDir 'makensis.exe' }
if (-not (Test-Path $makensis)) { throw "makensis.exe not found under $NsisDir" }
if (-not (Test-Path (Join-Path $SourceTree 'configure.ac'))) { throw "Not a smartmontools source tree: $SourceTree" }

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$work = Join-Path ([System.IO.Path]::GetTempPath()) ('sm-brand-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $work -Force | Out-Null

try {
    # 1. Unpack the official installer
    $payload = Join-Path $work 'payload'
    & $sevenZip x $OfficialSetup "-o$payload" -y | Out-Null
    if ($LASTEXITCODE -ne 0) { throw '7-Zip extraction failed.' }

    # 2. Rebuild the two input trees.
    #    installer.nsi takes 32-bit files from INPDIR and 64-bit from INPDIR64,
    #    sharing the docs and the helper scripts from INPDIR.
    $p32 = Join-Path $work 'p32'; $p64 = Join-Path $work 'p64'
    foreach ($d in @("$p32\bin", "$p32\doc", "$p64\bin", "$p64\doc")) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
    Copy-Item (Join-Path $payload 'bin32\*') (Join-Path $p32 'bin') -Force
    Get-ChildItem (Join-Path $payload 'bin') -File |
        Where-Object { $_.Extension -ne '.exe' } |
        Copy-Item -Destination (Join-Path $p32 'bin') -Force
    Copy-Item (Join-Path $payload 'doc\*') (Join-Path $p32 'doc') -Force
    Copy-Item (Join-Path $payload 'bin\*.exe') (Join-Path $p64 'bin') -Force
    Copy-Item (Join-Path $payload 'doc\checksums64.txt') (Join-Path $p64 'doc') -Force

    # 3. Apply the brand patches to a scratch copy of the source tree
    $branded = Join-Path $work 'branded'
    & python (Join-Path $repo 'scripts\apply_patches.py') $SourceTree $branded
    if ($LASTEXITCODE -ne 0) { throw 'Applying patches failed.' }

    $nsi = Join-Path $branded 'os_win32\installer.nsi'
    $outDir = Split-Path -Parent ([System.IO.Path]::GetFullPath($OutFile))
    $outName = Split-Path -Leaf $OutFile
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null

    # 4. Compile. Run from outDir so OriginalFilename stays a bare file name
    #    instead of leaking the build machine's path into the VERSIONINFO.
    $env:NSISDIR = $NsisDir
    Push-Location $outDir
    try {
        & $makensis -V2 -NOCD `
            "-DINPDIR=$p32" "-DINPDIR64=$p64" "-DOUTFILE=$outName" `
            "-DVERSION=$Version" "-DYY=$Year" "-DVERSTR=$VerString" `
            $nsi
        if ($LASTEXITCODE -ne 0) { throw "makensis failed with exit code $LASTEXITCODE" }
    }
    finally {
        Pop-Location
    }

    $result = Join-Path $outDir $outName
    if (-not (Test-Path $result)) { throw 'Installer was not produced.' }

    $info = Get-Item $result
    [pscustomobject]@{
        Path        = $info.FullName
        Size        = $info.Length
        SHA256      = (Get-FileHash $result -Algorithm SHA256).Hash
        ProductName = $info.VersionInfo.ProductName
        CompanyName = $info.VersionInfo.CompanyName
        Signed      = (Get-AuthenticodeSignature $result).Status.ToString()
    }
}
finally {
    Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
}
