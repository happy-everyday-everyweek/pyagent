<#
.SYNOPSIS
    PyAgent 自动化构建脚本
    
.DESCRIPTION
    自动完成以下构建任务：
    - 编译Python项目（构建wheel包）
    - 打包EXE可执行文件
    - 打包APK安装包
    
.PARAMETER SkipWheel
    跳过构建wheel包

.PARAMETER SkipExe
    跳过构建EXE

.PARAMETER SkipApk
    跳过构建APK

.PARAMETER NoClean
    不清理旧的构建文件

.EXAMPLE
    .\build.ps1
    执行所有构建任务

.EXAMPLE
    .\build.ps1 -SkipExe
    不构建EXE

.EXAMPLE
    .\build.ps1 -NoClean
    不清理旧的构建文件
#>

param(
    [switch]$SkipWheel,
    [switch]$SkipExe,
    [switch]$SkipApk,
    [switch]$NoClean
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build"

$env:JAVA_HOME = "D:\jdk-17.0.2"
$env:ANDROID_HOME = "D:\android-sdk"
$env:Path = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\build-tools\34.0.0;$env:Path"

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PyInstaller = Join-Path $ProjectRoot ".venv\Scripts\pyinstaller.exe"
$Gradle = "D:\rub\gradle-8.7\bin\gradle.bat"

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

function Clean-Build {
    Write-Header "Cleaning Build Files"
    
    $dirsToClean = @(
        $BuildDir,
        $DistDir,
        (Join-Path $ProjectRoot "android\app\build"),
        (Join-Path $ProjectRoot "android\.gradle"),
        (Join-Path $ProjectRoot "android\build")
    )
    
    foreach ($dir in $dirsToClean) {
        if (Test-Path $dir) {
            Write-Info "Removing: $dir"
            Remove-Item -Path $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    Write-Success "Clean completed"
}

function Build-Wheel {
    Write-Header "Building Wheel Package"
    
    if (-not (Test-Path $VenvPython)) {
        Write-Error-Custom "Python not found: $VenvPython"
        exit 1
    }
    
    Write-Info "Creating wheel package..."
    
    $buildArgs = @("-m", "build", "--wheel", "--outdir", $DistDir)
    
    & $VenvPython $buildArgs
    
    if ($LASTEXITCODE -eq 0) {
        $wheelFile = Get-ChildItem -Path $DistDir -Filter "*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($wheelFile) {
            Write-Success "Wheel package created: $($wheelFile.FullName)"
        }
    }
    else {
        Write-Error-Custom "Wheel build failed"
        exit 1
    }
}

function Build-Exe {
    Write-Header "Building EXE Package"
    
    if (-not (Test-Path $PyInstaller)) {
        Write-Error-Custom "PyInstaller not found: $PyInstaller"
        exit 1
    }
    
    $specFile = Join-Path $BuildDir "PyAgent.spec"
    $specDir = Split-Path -Parent $specFile
    
    if (-not (Test-Path $specDir)) {
        New-Item -ItemType Directory -Path $specDir -Force | Out-Null
    }
    
    Write-Info "Creating PyInstaller spec file..."
    
    $specContent = @'
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
project_root = Path(r'{PROJECT_ROOT}')

datas_list = []
if (project_root / 'config').exists():
    datas_list.append((str(project_root / 'config'), 'config'))
if (project_root / 'data').exists():
    datas_list.append((str(project_root / 'data'), 'data'))

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PyAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PyAgent',
)
'@
    
    $specContent = $specContent -replace '\{PROJECT_ROOT\}', $ProjectRoot
    Set-Content -Path $specFile -Value $specContent -Encoding UTF8
    
    Write-Info "Running PyInstaller..."
    
    $workPath = Join-Path $BuildDir "pyinstaller"
    $distPath = Join-Path $DistDir "exe"
    
    & $PyInstaller --distpath $distPath --workpath $workPath $specFile
    
    if ($LASTEXITCODE -eq 0) {
        $exeFile = Join-Path $distPath "PyAgent\PyAgent.exe"
        if (Test-Path $exeFile) {
            Write-Success "EXE created: $exeFile"
        }
    }
    else {
        Write-Error-Custom "EXE build failed"
        exit 1
    }
}

function Build-Apk {
    Write-Header "Building APK Package"
    
    $androidDir = Join-Path $ProjectRoot "android"
    
    if (-not (Test-Path $androidDir)) {
        Write-Error-Custom "Android project not found: $androidDir"
        exit 1
    }
    
    if (-not (Test-Path $Gradle)) {
        Write-Error-Custom "Gradle not found: $Gradle"
        exit 1
    }
    
    Write-Info "Running Gradle build..."
    
    Push-Location $androidDir
    
    try {
        & $Gradle assembleDebug --no-daemon
        
        if ($LASTEXITCODE -eq 0) {
            $apkFile = Join-Path $androidDir "app\build\outputs\apk\debug\app-debug.apk"
            if (Test-Path $apkFile) {
                Write-Success "APK created: $apkFile"
            }
        }
        else {
            Write-Error-Custom "APK build failed"
            exit 1
        }
    }
    finally {
        Pop-Location
    }
}

function Main {
    $startTime = Get-Date
    
    Write-Header "PyAgent Build Script"
    Write-Info "Project Root: $ProjectRoot"
    Write-Info "Build Wheel: $(-not $SkipWheel)"
    Write-Info "Build EXE: $(-not $SkipExe)"
    Write-Info "Build APK: $(-not $SkipApk)"
    Write-Info "Clean: $(-not $NoClean)"
    
    if (-not $NoClean) {
        Clean-Build
    }
    
    if (-not (Test-Path $DistDir)) {
        New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
    }
    
    if (-not (Test-Path $BuildDir)) {
        New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
    }
    
    if (-not $SkipWheel) {
        Build-Wheel
    }
    
    if (-not $SkipExe) {
        Build-Exe
    }
    
    if (-not $SkipApk) {
        Build-Apk
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Header "Build Summary"
    Write-Host "Total Duration: $($duration.ToString('mm\:ss'))"
    Write-Host ""
    Write-Host "Output Files:" -ForegroundColor Cyan
    
    if (-not $SkipWheel) {
        $wheelFile = Get-ChildItem -Path $DistDir -Filter "*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($wheelFile) {
            Write-Host "  Wheel: $($wheelFile.FullName)" -ForegroundColor White
        }
    }
    
    if (-not $SkipExe) {
        $exeFile = Join-Path $DistDir "exe\PyAgent\PyAgent.exe"
        if (Test-Path $exeFile) {
            Write-Host "  EXE: $exeFile" -ForegroundColor White
        }
    }
    
    if (-not $SkipApk) {
        $apkFile = Join-Path $ProjectRoot "android\app\build\outputs\apk\debug\app-debug.apk"
        if (Test-Path $apkFile) {
            Write-Host "  APK: $apkFile" -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Success "Build completed successfully!"
}

Main
