@echo off
REM Build script for PhotoPuller executable
REM This creates a standalone .exe file that can run on Windows without Python installed

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building PhotoPuller executable...
pyinstaller --name=PhotoPuller ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "README.md;." ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    main.py

echo.
echo Build complete! The executable is in the 'dist' folder.
echo You can distribute PhotoPuller.exe to other Windows computers.
pause


