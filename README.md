# PhotoPuller

A simple Windows application to find and organize important photos and videos from a drive, excluding system files, program files, and temporary internet files.

## Features

- **Smart File Detection**: Automatically finds photos, videos, and PDFs on any drive
- **Intelligent Filtering**: Excludes files from installed programs, system files, and temporary internet files
- **Organized Copying**: Copies files to a destination drive with a sensible folder structure
- **Duplicate Detection**: Avoids copying duplicate files using hash comparison
- **Progress Tracking**: Real-time progress updates during scanning and copying
- **Flexible Organization**: Choose to organize by date (Year/Month) or by source drive
- **Dual Mode Operation**: Run with a GUI for interactive use or headless via CLI for automation
- **MCP Server Support**: Expose PhotoPuller functionality to AI agents via Model Context Protocol
- **Dry Run Mode**: Preview what would be copied without actually copying files
- **Selective File Types**: Choose which file types to scan (photos, videos, PDFs)

## Supported File Types

### Photos
- Common formats: JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP
- Camera RAW formats: CR2, NEF, ORF, SR2, ARW, DNG
- Other: HEIC, HEIF, PSD, XCF

### Videos
- Common formats: MP4, AVI, MOV, WMV, FLV, MKV, WEBM, M4V
- Other: MPG, MPEG, 3GP, ASF, RM, VOB, TS, MTS, M2TS

### PDFs
- PDF documents: PDF

## Installation

### Running from Source

1. Ensure you have Python 3.7 or higher installed
2. Clone or download this repository
3. No additional packages required - uses only Python standard library!

### Creating a Standalone Executable

To create a portable `.exe` file that can run on any Windows computer without Python installed:

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable** (choose one method):
   
   **Option A - Using the build script** (easiest):
   ```bash
   build_exe.bat
   ```
   
   **Option B - Using PyInstaller directly**:
   ```bash
   pyinstaller --name=PhotoPuller --onefile --windowed main.py
   ```
   
   **Option C - Using the spec file** (for customization):
   ```bash
   pyinstaller PhotoPuller.spec
   ```

3. **Find your executable**: After building, the `PhotoPuller.exe` file will be in the `dist` folder.

4. **Distribute**: You can copy `PhotoPuller.exe` to any Windows computer and run it directly - no Python installation needed!

**Note**: The first time you run PyInstaller, it may take a few minutes to build. The resulting `.exe` file will be larger (typically 10-20 MB) because it includes Python and all necessary libraries bundled inside.

## Usage

PhotoPuller can run in two modes: **GUI mode** (interactive) and **CLI mode** (headless/command-line).

### GUI Mode (Interactive)

1. Run the application:
   ```bash
   python main.py
   ```

2. **Select Source Drive**: 
   - Enter or browse for the drive/directory you want to scan (e.g., `C:\` or `D:\`)
   - Click "Scan Drive" to start scanning

3. **Review Results**:
   - The application will display all found photos, videos, and PDFs
   - Review the statistics and file list
   - Use checkboxes to filter which file types to scan for

4. **Select Destination**:
   - Choose where you want to copy the files
   - Select organization method:
     - **Date**: Organizes by Year/Month (e.g., `Photos/2024/03/`)
     - **Source**: Organizes by source drive (e.g., `Photos/C/`)

5. **Copy Files**:
   - Click "Copy Files" to start the copying process
   - The application will show progress and statistics

### CLI Mode (Headless)

Run PhotoPuller from the command line for automation or scripting:

```bash
python photopuller_cli.py -s SOURCE -d DESTINATION [OPTIONS]
```

**Required Arguments:**
- `-s, --source`: Source path to scan (drive or directory)
- `-d, --destination`: Destination path to copy files to

**File Type Filters:**
- `--photos`: Include photos in scan
- `--videos`: Include videos in scan
- `--pdfs`: Include PDFs in scan
- If none specified, all types are included by default

**Other Options:**
- `--exclude PATH [PATH ...]`: List of folder paths to exclude
- `--organize-by {date,source}`: Organization method (default: date)
- `--dry-run`: Scan and report what would be copied without actually copying
- `--json`: Output results in JSON format
- `-q, --quiet`: Suppress progress output

**Examples:**

```bash
# Scan and copy photos and videos from C: to D:\Backup
python photopuller_cli.py -s C:\ -d D:\Backup --photos --videos

# Dry run to see what would be copied
python photopuller_cli.py -s C:\ -d D:\Backup --dry-run

# Scan only PDFs with excluded folders
python photopuller_cli.py -s C:\ -d D:\Backup --pdfs --exclude "C:\Windows" "C:\Program Files"

# Organize by source drive instead of date
python photopuller_cli.py -s C:\ -d D:\Backup --organize-by source

# Output results as JSON for scripting
python photopuller_cli.py -s C:\ -d D:\Backup --json > results.json
```

## MCP Server (AI Agent Integration)

PhotoPuller includes an MCP (Model Context Protocol) server that allows AI agents to interact with the application programmatically. This enables AI assistants like Claude to help users organize their files.

### Quick Start

1. **Test the MCP Server**:
   ```bash
   python test_mcp_server.py
   ```

2. **Configure Claude Desktop** (see `MCP_SETUP.md` for details):
   - Add PhotoPuller to your Claude Desktop configuration
   - Restart Claude Desktop
   - AI agents can now use PhotoPuller tools

### Available MCP Tools

- `photopuller_scan` - Scan drives for photos, videos, and PDFs
- `photopuller_get_scan_stats` - Get scan statistics
- `photopuller_copy_files` - Copy files to organized destination
- `photopuller_get_copy_stats` - Get copy operation statistics
- `photopuller_add_exclusion` - Add folder to exclusion list
- `photopuller_remove_exclusion` - Remove folder from exclusions
- `photopuller_clear_exclusions` - Clear all exclusions

### Example AI Interaction

An AI agent can help users by:
1. Asking what drive/folder to scan
2. Calling `photopuller_scan` with user's preferences
3. Showing scan results and statistics
4. Asking for destination and organization preferences
5. Running a dry-run first to preview
6. Copying files when user confirms

For detailed setup instructions, see [MCP_SETUP.md](MCP_SETUP.md).

## Folder Structure

### By Date (Default)
```
Destination/
├── Photos/
│   ├── 2024/
│   │   ├── 01/
│   │   ├── 02/
│   │   └── 03/
│   └── 2023/
│       └── 12/
├── Videos/
│   ├── 2024/
│   └── 2023/
├── PDFs/
│   ├── 2024/
│   └── 2023/
└── Downloads/
    └── (all files from downloads folders)
```

### By Source
```
Destination/
├── Photos/
│   ├── C/
│   └── D/
├── Videos/
│   ├── C/
│   └── D/
├── PDFs/
│   ├── C/
│   └── D/
└── Downloads/
    └── (all files from downloads folders)
```

**Note**: Files originating from "downloads" folders are automatically placed in a top-level "Downloads" folder, regardless of organization method.

## Excluded Paths

The application automatically excludes:
- Windows system directories
- Program Files directories
- Temporary files and caches
- Browser cache and history folders
- Hidden and system files
- Files smaller than 1KB (likely thumbnails)
- Thumbnail database files

## Safety Features

- **Duplicate Detection**: Uses MD5 hashing to detect and skip duplicate files
- **Permission Handling**: Gracefully handles permission errors
- **Progress Tracking**: Real-time updates so you know what's happening
- **Error Reporting**: Shows detailed statistics after operations

## Notes

- The application runs scanning and copying in separate threads to keep the UI responsive
- Large drives may take a while to scan - be patient!
- Some directories may be inaccessible due to permissions - this is normal
- The application preserves file modification dates when copying

## Troubleshooting

- **Permission Errors**: Some system directories require administrator privileges. The app will skip these automatically.
- **Slow Scanning**: Large drives with many files can take time. The progress bar will show activity.
- **No Files Found**: Check that you're scanning a drive that contains photos/videos, and that they're not all in excluded directories.

## License

This project is provided as-is for personal use.
