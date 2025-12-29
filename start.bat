@echo off
setlocal

set VENV_NAME=venv
set PYTHON_VERSION=3.14
set ENTRY_SCRIPT=battaStart.py

echo Checking for Python %PYTHON_VERSION%...
py -%PYTHON_VERSION% --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo ERROR: Python %PYTHON_VERSION% is not installed or not available via the py launcher.
    echo Install it from https://www.python.org
    echo Or change PYTHON_VERSION in this script.
    echo.
    pause
    exit /b 1
)


if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo.
    echo Virtual environment not found. Creating it...
    py -%PYTHON_VERSION% -m venv %VENV_NAME%
    IF ERRORLEVEL 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )

    echo Activating virtual environment...
    call "%VENV_NAME%\Scripts\activate.bat"

    echo Upgrading pip...
    python -m pip install --upgrade pip

    if not exist "requirements.txt" (
        echo.
        echo ERROR: requirements.txt not found.
        pause
        exit /b 1
    )

    echo Installing dependencies...
    pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment found.
)


call "%VENV_NAME%\Scripts\activate.bat"
IF ERRORLEVEL 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)


if not exist "%ENTRY_SCRIPT%" (
    echo.
    echo ERROR: %ENTRY_SCRIPT% not found in current directory.
    pause
    exit /b 1
)


echo.
echo =====================================
echo Starting %ENTRY_SCRIPT%
python --version
echo =====================================
echo.

python "%ENTRY_SCRIPT%"

echo.
echo Program exited.
pause

endlocal