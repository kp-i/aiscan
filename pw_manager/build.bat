@echo off
REM VaultKey build script for Windows
REM Run this from the pw_manager directory

echo [VaultKey] Installing dependencies...
pip install -r requirements.txt

echo.
echo [VaultKey] Building executable...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name VaultKey ^
  --add-data "src;src" ^
  main.py

echo.
if exist "dist\VaultKey.exe" (
  echo [VaultKey] Build successful!
  echo Output: dist\VaultKey.exe
) else (
  echo [VaultKey] Build FAILED. Check the output above.
  exit /b 1
)
