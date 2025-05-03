@echo off
setlocal

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="test" goto test
if "%1"=="test-cov" goto test-cov
if "%1"=="test-unit" goto test-unit
if "%1"=="test-integration" goto test-integration
if "%1"=="lint" goto lint
if "%1"=="format" goto format
if "%1"=="clean" goto clean

:help
echo Available commands:
echo   run_tests.bat test              Run all tests
echo   run_tests.bat test-cov          Run tests with coverage report
echo   run_tests.bat test-unit         Run unit tests only
echo   run_tests.bat test-integration  Run integration tests only
echo   run_tests.bat lint              Run linting checks
echo   run_tests.bat format            Format code with black and isort
echo   run_tests.bat clean             Clean up cache and temporary files
goto end

:test
pytest
goto end

:test-cov
pytest --cov=app --cov-report=term-missing --cov-report=html:coverage_html
goto end

:test-unit
pytest tests\unit
goto end

:test-integration
pytest tests\integration
goto end

:lint
flake8 app tests
mypy app tests
black --check app tests
isort --check-only app tests
goto end

:format
black app tests
isort app tests
goto end

:clean
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .coverage del /f .coverage
if exist coverage.xml del /f coverage.xml
if exist coverage_html rmdir /s /q coverage_html
if exist .mypy_cache rmdir /s /q .mypy_cache
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>&1
goto end

:end
endlocal
