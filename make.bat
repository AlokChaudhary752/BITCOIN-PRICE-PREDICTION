@echo off
set PYTHON="%~dp0.venv\Scripts\python.exe"

if "%1"=="train" (
    %PYTHON% -m btc_oracle_ml.train %2
    exit /b %ERRORLEVEL%
)

if "%1"=="test-ml" (
    %PYTHON% -m pytest packages/ml/tests -v
    exit /b %ERRORLEVEL%
)

if "%1"=="install" (
    %PYTHON% -m pip install -r packages\ml\requirements.txt
    %PYTHON% -m pip install -e packages\ml
    exit /b %ERRORLEVEL%
)

echo Unknown command: %1
echo Usage: make.bat [train ^| test-ml ^| install]
exit /b 1
