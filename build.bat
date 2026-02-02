@echo off
echo Building ESP32 Uploader...
echo.
echo NOTE: Installing pyinstaller if missing...
pip install pyinstaller

echo.
echo Running PyInstaller with --collect-all for esptool and customtkinter...
pyinstaller --noconfirm --onefile --windowed --collect-all esptool --collect-all customtkinter --name "ESP32 Uploader" src/main.py

echo.
echo Build Complete!
echo Run the app from: dist\ESP32 Uploader\ESP32 Uploader.exe
pause
