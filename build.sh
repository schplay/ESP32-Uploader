#!/bin/bash

# macOS/Linux Build Script for ESP32 Uploader

echo "Building ESP32 Uploader..."
echo ""

# Ensure PyInstaller is installed
echo "Checking for PyInstaller..."
pip3 install pyinstaller

echo ""
echo "Running PyInstaller..."
# Same arguments as Windows, just using standard shell syntax
# --collect-all esptool is CRITICAL for finding the stub files
pyinstaller --noconfirm --onefile --windowed --collect-all esptool --collect-all customtkinter --name "ESP32_Uploader" src/main.py

echo ""
echo "Build Complete!"
echo "You can find your executable in the 'dist' folder."
echo "Note: On macOS, you might see 'ESP32_Uploader.app' or a Unix executable depending on your config."
