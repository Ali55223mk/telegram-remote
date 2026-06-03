@echo off
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo Done!
) else (
    echo Try: python -m pip install -r requirements.txt
)
pause
