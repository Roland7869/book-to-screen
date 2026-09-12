@echo off
REM Builds a standalone Book-to-Screen AI Production Pipeline.exe (no Python needed to run it).
REM Requires PyInstaller (already installed): pip install pyinstaller
echo Building executable (this may take a minute)...
python -m PyInstaller --noconfirm --onefile --windowed --icon book_to_script.ico --name book-to-screen book_to_script_app.py
if %errorlevel% neq 0 (
    echo.
    echo Build failed. See the messages above.
    pause
    exit /b 1
)
echo.
echo Done. Your app is: dist\book_to_script_app.exe
echo Double-click it to run.
pause
