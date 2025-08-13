@echo off
echo Cinema Data Generator - Scraper Runner
echo =====================================

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment. Make sure Python is installed.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Check if requirements are installed, if not install them
echo Checking and installing requirements...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo Error: Failed to install requirements.
    pause
    exit /b 1
)

REM Run the scraper scripts
echo Starting cinema data scraping...
echo.

echo Running Cinepolis scraper...
python cinepolis.py
if errorlevel 1 (
    echo Warning: Cinepolis scraper encountered an error.
)

echo.
echo Running Cinemark scraper...
python cinemark.py
if errorlevel 1 (
    echo Warning: Cinemark scraper encountered an error.
)

echo.
echo Scraping completed!
echo Check the generated Excel files for results.
pause
