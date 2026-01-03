# Building PhotoPuller Executable

This guide explains how to package PhotoPuller into a standalone Windows executable that can run on any computer without Python installed.

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Quick Start

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Run the build script**:
   ```bash
   build_exe.bat
   ```

3. **Find your executable**: The `PhotoPuller.exe` file will be in the `dist` folder.

## Manual Build

If you prefer to build manually:

```bash
pyinstaller --name=PhotoPuller --onefile --windowed main.py
```

Or using the spec file for more control:

```bash
pyinstaller PhotoPuller.spec
```

## Build Options Explained

- `--onefile`: Creates a single executable file (easier to distribute)
- `--windowed`: Hides the console window (GUI only)
- `--name=PhotoPuller`: Sets the name of the executable

## Output

After building, you'll find:
- `PhotoPuller.exe` in the `dist` folder - This is your distributable executable
- `build` folder - Temporary build files (can be deleted)
- `PhotoPuller.spec` - Build configuration (can be customized)

## Distribution

Simply copy `PhotoPuller.exe` to any Windows computer. No installation needed!

**File Size**: The executable will be approximately 10-20 MB because it includes Python and all necessary libraries bundled inside.

## Troubleshooting

### Antivirus Warnings
Some antivirus software may flag PyInstaller executables as suspicious. This is a false positive. You can:
- Add an exception in your antivirus
- Use a code signing certificate (for production releases)

### Missing Modules
If you get import errors, add them to the `hiddenimports` list in `PhotoPuller.spec`:
```python
hiddenimports=[
    'tkinter',
    'tkinter.ttk',
    # Add any missing modules here
],
```

### File Size Too Large
To reduce file size, you can:
- Use `--exclude-module` to exclude unused modules
- Use UPX compression (already enabled in the spec file)

## Advanced: Custom Icon

To add a custom icon to your executable:

1. Create or obtain an `.ico` file
2. Update `PhotoPuller.spec`:
   ```python
   icon='path/to/your/icon.ico',
   ```
3. Rebuild using the spec file



