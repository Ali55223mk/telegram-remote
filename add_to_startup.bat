@echo off
cd /d "%~dp0"
set SCRIPT_PATH="%~dp0run_bot.vbs"
echo Creating startup script...

REM Create a VBS script that runs without a console window
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo WshShell.Run chr^(34^) ^& "%~dp0bot.py" ^& chr^(34^), 0, False
) > "%TEMP%\run_bot_temp.vbs"

powershell -Command ^
  $wshell = New-Object -ComObject WScript.Shell; ^
  $shortcut = $wshell.CreateShortcut([Environment]::GetFolderPath('Startup') + '\TelegramRemote.lnk'); ^
  $shortcut.TargetPath = 'pythonw.exe'; ^
  $shortcut.Arguments = '"%~dp0bot.py"'; ^
  $shortcut.WorkingDirectory = '%~dp0'; ^
  $shortcut.WindowStyle = 7; ^
  $shortcut.Save(); ^
  Write-Host 'Done! Added to startup.'

echo.
echo تمت الإضافة! سيشتغل البوت تلقائياً عند تشغيل الويندوز.
pause
