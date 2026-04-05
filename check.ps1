<#
.SYNOPSIS
    PyAgent 测试和代码风格检查脚本 v2.0

.DESCRIPTION
    运行所有测试和代码风格检查工具，包括：
    - pytest: 单元测试
    - ruff: 代码风格检查和格式化
    - mypy: 类型检查
    - bandit: 安全检查
    - pydocstyle: 文档字符串检查

.PARAMETER SkipTests
    跳过测试运行

.PARAMETER SkipLint
    跳过代码风格检查

.PARAMETER SkipTypeCheck
    跳过类型检查

.PARAMETER SkipSecurity
    跳过安全检查

.PARAMETER SkipDocs
    跳过文档字符串检查

.PARAMETER Fix
    自动修复可修复的问题（ruff格式化）

.PARAMETER Coverage
    生成测试覆盖率报告

.PARAMETER Verbose
    显示详细输出

.PARAMETER FailUnder
    覆盖率阈值，低于此值则失败

.PARAMETER Parallel
    并行运行测试

.PARAMETER Benchmark
    运行性能基准测试

.PARAMETER Mutation
    运行变异测试

.EXAMPLE
    .\check.ps1
    运行所有检查

.EXAMPLE
    .\check.ps1 -SkipTests -Fix
    跳过测试，自动修复代码风格问题

.EXAMPLE
    .\check.ps1 -Coverage -FailUnder 80
    运行测试并生成覆盖率报告，覆盖率低于80%则失败
#>

param(
    [switch]$SkipTests,
    [switch]$SkipLint,
    [switch]$SkipTypeCheck,
    [switch]$SkipSecurity,
    [switch]$SkipDocs,
    [switch]$Fix,
    [switch]$Coverage,
    [switch]$Verbose,
    [int]$FailUnder = 0,
    [switch]$Parallel,
    [switch]$Benchmark,
    [switch]$Mutation
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

$TotalErrors = 0
$TotalWarnings = 0
$StartTime = Get-Date
$TestResults = @{}

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Result {
    param(
        [string]$Name,
        [int]$Errors = 0,
        [int]$Warnings = 0,
        [bool]$Success = $true,
        [float]$Coverage = -1
    )
    
    $coverageStr = if ($Coverage -ge 0) { " | Coverage: $([math]::Round($Coverage, 1))%" } else { "" }
    
    if ($Success -and $Errors -eq 0 -and $Warnings -eq 0) {
        Write-Host "[PASS] $Name$coverageStr" -ForegroundColor Green
    } elseif ($Errors -gt 0) {
        Write-Host "[FAIL] $Name - $Errors error(s), $Warnings warning(s)$coverageStr" -ForegroundColor Red
    } else {
        Write-Host "[WARN] $Name - $Warnings warning(s)$coverageStr" -ForegroundColor Yellow
    }
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Install-DevDependencies {
    Write-Header "Checking Development Dependencies"
    
    $devPackages = @(
        @{Name = "pytest"; Module = "pytest"; Version = ">=8.0.0"},
        @{Name = "pytest-asyncio"; Module = "pytest_asyncio"; Version = ">=0.23.0"},
        @{Name = "pytest-cov"; Module = "pytest_cov"; Version = ">=4.1.0"},
        @{Name = "pytest-timeout"; Module = "pytest_timeout"; Version = ">=2.3.0"},
        @{Name = "pytest-xdist"; Module = "xdist"; Version = ">=3.5.0"},
        @{Name = "ruff"; Module = "ruff"; Version = ">=0.4.0"},
        @{Name = "mypy"; Module = "mypy"; Version = ">=1.10.0"},
        @{Name = "bandit"; Module = "bandit"; Version = ">=1.7.0"},
        @{Name = "pydocstyle"; Module = "pydocstyle"; Version = ">=6.3.0"}
    )
    
    foreach ($package in $devPackages) {
        $packageName = $package.Name
        $moduleName = $package.Module
        Write-Host "Checking $packageName..." -NoNewline
        
        try {
            $null = & $VenvPython -c "import $moduleName" 2>$null
            Write-Host " OK" -ForegroundColor Green
        } catch {
            Write-Host " INSTALLING" -ForegroundColor Yellow
            $installPackage = "$packageName$($package.Version)"
            & $VenvPython -m pip install $installPackage --quiet 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Failed to install $packageName" -ForegroundColor Red
                exit 1
            }
            Write-Host " DONE" -ForegroundColor Green
        }
    }
}

function Invoke-Tests {
    Write-Header "Running Tests"
    
    $testPath = Join-Path $ProjectRoot "tests"
    
    if (-not (Test-Path $testPath)) {
        Write-Host "No tests directory found" -ForegroundColor Yellow
        return @{ Errors = 0; Warnings = 0; Success = $true; Coverage = -1 }
    }
    
    $testFiles = Get-ChildItem -Path $testPath -Filter "test_*.py" -Recurse
    if ($testFiles.Count -eq 0) {
        Write-Host "No test files found" -ForegroundColor Yellow
        return @{ Errors = 0; Warnings = 0; Success = $true; Coverage = -1 }
    }
    
    Write-Host "Found $($testFiles.Count) test file(s):" -ForegroundColor Gray
    $testFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    Write-Host ""
    
    $pytestArgs = @("tests", "-v", "--timeout=60")
    
    if ($Coverage) {
        $pytestArgs += @(
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=json:coverage.json"
        )
        Write-Host "Coverage report will be generated in htmlcov/" -ForegroundColor Gray
    }
    
    if ($FailUnder -gt 0) {
        $pytestArgs += "--cov-fail-under=$FailUnder"
        Write-Host "Coverage threshold: $FailUnder%" -ForegroundColor Gray
    }
    
    if ($Parallel) {
        $pytestArgs += "-n=auto"
        Write-Host "Running tests in parallel" -ForegroundColor Gray
    }
    
    if ($Verbose) {
        $pytestArgs += "--tb=long"
    } else {
        $pytestArgs += "--tb=short"
    }
    
    $output = & $VenvPython -m pytest @pytestArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    Write-Host $output
    
    $failed = ($output | Select-String "failed").Count
    $errors = ($output | Select-String "error").Count
    $warnings = ($output | Select-String "warning").Count
    
    $coverageValue = -1
    if ($Coverage -and (Test-Path "coverage.json")) {
        try {
            $coverageData = Get-Content "coverage.json" | ConvertFrom-Json
            $coverageValue = $coverageData.totals.percent_covered
        } catch {
            $coverageValue = -1
        }
    }
    
    Write-Result -Name "pytest" -Errors $failed -Warnings $warnings -Success ($exitCode -eq 0) -Coverage $coverageValue
    
    $TestResults["pytest"] = @{
        ExitCode = $exitCode
        Failed = $failed
        Warnings = $warnings
        Coverage = $coverageValue
    }
    
    return @{ Errors = $failed; Warnings = $warnings; Success = ($exitCode -eq 0); Coverage = $coverageValue }
}

function Invoke-Ruff {
    Write-Header "Running Ruff (Code Style Check)"
    
    $ruffArgs = @("check", "src", "tests", "--statistics")
    
    if ($Fix) {
        $ruffArgs += "--fix"
        Write-Host "Auto-fix mode enabled" -ForegroundColor Yellow
    }
    
    $output = & $VenvPython -m ruff @ruffArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($output) {
        Write-Host $output
    } else {
        Write-Host "No issues found" -ForegroundColor Green
    }
    
    $errors = ($output | Select-String "error").Count
    $warnings = ($output | Select-String "warning").Count
    
    Write-Result -Name "ruff" -Errors $errors -Warnings $warnings -Success ($exitCode -eq 0)
    
    return @{ Errors = $errors; Warnings = $warnings; Success = ($exitCode -eq 0) }
}

function Invoke-RuffFormat {
    Write-Header "Running Ruff Format"
    
    $ruffArgs = @("format", "src", "tests", "--check")
    
    if ($Fix) {
        $ruffArgs = @("format", "src", "tests")
    }
    
    $output = & $VenvPython -m ruff @ruffArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($output) {
        Write-Host $output
    }
    
    if ($exitCode -eq 0) {
        Write-Host "All files formatted correctly" -ForegroundColor Green
    } else {
        Write-Host "Some files need formatting. Run with -Fix to auto-format." -ForegroundColor Yellow
    }
    
    Write-Result -Name "ruff-format" -Errors $(if ($exitCode -ne 0) { 1 } else { 0 }) -Warnings 0 -Success ($exitCode -eq 0)
    
    return @{ Errors = $(if ($exitCode -ne 0) { 1 } else { 0 }); Warnings = 0; Success = ($exitCode -eq 0) }
}

function Invoke-Mypy {
    Write-Header "Running MyPy (Type Check)"
    
    $mypyArgs = @("src", "--ignore-missing-imports")
    
    if ($Verbose) {
        $mypyArgs += "--verbose"
    }
    
    $output = & $VenvPython -m mypy @mypyArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    Write-Host $output
    
    $errors = ($output | Select-String "error:").Count
    $warnings = ($output | Select-String "warning:").Count
    
    Write-Result -Name "mypy" -Errors $errors -Warnings $warnings -Success ($exitCode -eq 0)
    
    return @{ Errors = $errors; Warnings = $warnings; Success = ($exitCode -eq 0) }
}

function Invoke-Bandit {
    Write-Header "Running Bandit (Security Check)"
    
    $banditArgs = @("-r", "src", "-ll", "-q")
    
    $output = & $VenvPython -m bandit @banditArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    Write-Host $output
    
    $high = ($output | Select-String "Severity: High").Count
    $medium = ($output | Select-String "Severity: Medium").Count
    $low = ($output | Select-String "Severity: Low").Count
    
    $errors = $high + $medium
    $warnings = $low
    
    Write-Result -Name "bandit" -Errors $errors -Warnings $warnings -Success ($exitCode -eq 0)
    
    return @{ Errors = $errors; Warnings = $warnings; Success = ($exitCode -eq 0) }
}

function Invoke-Pydocstyle {
    Write-Header "Running Pydocstyle (Docstring Check)"
    
    $pydocstyleArgs = @("src", "--ignore=D100,D104,D107,D203,D213")
    
    $output = & $VenvPython -m pydocstyle @pydocstyleArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($output) {
        Write-Host $output
    } else {
        Write-Host "All docstrings are properly formatted" -ForegroundColor Green
    }
    
    $errors = ($output | Select-String "D").Count
    $warnings = 0
    
    Write-Result -Name "pydocstyle" -Errors $errors -Warnings $warnings -Success ($exitCode -eq 0)
    
    return @{ Errors = $errors; Warnings = $warnings; Success = ($exitCode -eq 0) }
}

function Invoke-ComplexityCheck {
    Write-Header "Running Complexity Check (Ruff PLR)"
    
    $ruffArgs = @("check", "src", "--select=PLR", "--statistics")
    
    $output = & $VenvPython -m ruff @ruffArgs 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($output) {
        Write-Host $output
    } else {
        Write-Host "No complexity issues found" -ForegroundColor Green
    }
    
    $errors = ($output | Select-String "PLR").Count
    
    Write-Result -Name "complexity" -Errors $errors -Warnings 0 -Success ($exitCode -eq 0)
    
    return @{ Errors = $errors; Warnings = 0; Success = ($exitCode -eq 0) }
}

function Show-Summary {
    param(
        [int]$TotalErrors,
        [int]$TotalWarnings,
        [timespan]$Duration
    )
    
    Write-Header "Summary"
    
    Write-Host "Duration: $($Duration.ToString('mm\:ss'))" -ForegroundColor Gray
    Write-Host ""
    
    if ($TestResults["pytest"]) {
        $pytestResult = $TestResults["pytest"]
        Write-Host "Test Results:" -ForegroundColor Gray
        Write-Host "  Exit Code: $($pytestResult.ExitCode)" -ForegroundColor Gray
        Write-Host "  Failed Tests: $($pytestResult.Failed)" -ForegroundColor Gray
        if ($pytestResult.Coverage -ge 0) {
            Write-Host "  Coverage: $([math]::Round($pytestResult.Coverage, 1))%" -ForegroundColor Gray
        }
        Write-Host ""
    }
    
    if ($TotalErrors -eq 0 -and $TotalWarnings -eq 0) {
        Write-Host "All checks passed!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  /$$$$$$  /$$   /$$ /$$$$$$$$" -ForegroundColor Green
        Write-Host " /$$__  $$| $$  | $$|__  $$__/" -ForegroundColor Green
        Write-Host "| $$  \ $$| $$  | $$   | $$   " -ForegroundColor Green
        Write-Host "| $$  | $$| $$  | $$   | $$   " -ForegroundColor Green
        Write-Host "| $$  | $$| $$  | $$   | $$   " -ForegroundColor Green
        Write-Host "|  $$$$$$/|  $$$$$$/   | $$   " -ForegroundColor Green
        Write-Host " \______/  \______/    |__/   " -ForegroundColor Green
        Write-Host ""
        return 0
    } else {
        Write-Host "Total Errors: $TotalErrors" -ForegroundColor Red
        Write-Host "Total Warnings: $TotalWarnings" -ForegroundColor Yellow
        Write-Host ""
        
        if ($TotalErrors -gt 0) {
            Write-Host "Some checks failed. Please fix the issues above." -ForegroundColor Red
            return 1
        } else {
            Write-Host "All checks passed with warnings." -ForegroundColor Yellow
            return 0
        }
    }
}

# Main execution
Write-Host ""
Write-Host "  ____      _          _   _          _   " -ForegroundColor Cyan
Write-Host " |  _ \ ___| |__   ___| |_| |    __ _| |__" -ForegroundColor Cyan
Write-Host " | |_) / _ \ '_ \ / _ \ __| |   / _` | '_ \" -ForegroundColor Cyan
Write-Host " |  __/  __/ |_) |  __/ |_| |__| (_| | |_) |" -ForegroundColor Cyan
Write-Host " |_|   \___|_.__/ \___|\__|_____\__,_|_.__/" -ForegroundColor Cyan
Write-Host ""
Write-Host "PyAgent Test & Code Quality Check Script v2.0" -ForegroundColor Gray
Write-Host ""

# Install dependencies
Install-DevDependencies

# Run checks
if (-not $SkipTests) {
    $result = Invoke-Tests
    $TotalErrors += $result.Errors
    $TotalWarnings += $result.Warnings
}

if (-not $SkipLint) {
    $result = Invoke-Ruff
    $TotalErrors += $result.Errors
    $TotalWarnings += $result.Warnings
    
    $result = Invoke-RuffFormat
    $TotalErrors += $result.Errors
    $TotalWarnings += $result.Warnings
}

if (-not $SkipTypeCheck) {
    $result = Invoke-Mypy
    $TotalErrors += $result.Errors
    $TotalWarnings += $result.Warnings
}

if (-not $SkipSecurity) {
    $result = Invoke-Bandit
    $TotalErrors += $result.Errors
    $TotalWarnings += $result.Warnings
}

if (-not $SkipDocs) {
    $result = Invoke-Pydocstyle
    $TotalErrors += $result.Errors
    $TotalWarnings += $result.Warnings
}

# Run complexity check
$result = Invoke-ComplexityCheck
$TotalWarnings += $result.Errors

# Show summary
$EndTime = Get-Date
$Duration = $EndTime - $StartTime
$exitCode = Show-Summary -TotalErrors $TotalErrors -TotalWarnings $TotalWarnings -Duration $Duration

exit $exitCode
