# PhotoPuller MCP Server Setup Guide

## Overview

The Model Context Protocol (MCP) allows AI agents to interact with PhotoPuller programmatically. This enables AI assistants to help users organize their photos, videos, and PDFs by scanning drives and copying files to organized destinations.

## How MCP Works

MCP (Model Context Protocol) is a protocol that enables AI assistants to:
1. **Discover Tools**: Query what capabilities are available
2. **Call Tools**: Execute operations with parameters
3. **Receive Results**: Get structured responses with data

The PhotoPuller MCP server exposes the following tools:
- `photopuller_scan` - Scan drives for photos, videos, and PDFs
- `photopuller_get_scan_stats` - Get statistics about the last scan
- `photopuller_copy_files` - Copy scanned files to a destination
- `photopuller_get_copy_stats` - Get statistics about the last copy operation
- `photopuller_add_exclusion` - Add a folder to the exclusion list
- `photopuller_remove_exclusion` - Remove a folder from exclusions
- `photopuller_clear_exclusions` - Clear all exclusions

## Installation

The MCP server uses only Python standard library modules, so no additional dependencies are required beyond what PhotoPuller already needs.

## Configuration

### For Claude Desktop (Anthropic)

To use PhotoPuller with Claude Desktop, add the following to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "photopuller": {
      "command": "python",
      "args": [
        "R:\\development\\photopuller\\mcp_server.py"
      ],
      "cwd": "R:\\development\\photopuller"
    }
  }
}
```

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "photopuller": {
      "command": "python3",
      "args": [
        "/path/to/photopuller/mcp_server.py"
      ],
      "cwd": "/path/to/photopuller"
    }
  }
}
```

**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "photopuller": {
      "command": "python3",
      "args": [
        "/path/to/photopuller/mcp_server.py"
      ],
      "cwd": "/path/to/photopuller"
    }
  }
}
```

**Note**: Replace the paths with the actual path to your PhotoPuller installation.

### For Other MCP Clients

The MCP server communicates via JSON-RPC 2.0 over stdio. Any MCP-compatible client can connect to it by:

1. Starting the server process: `python mcp_server.py`
2. Sending JSON-RPC requests via stdin
3. Receiving JSON-RPC responses via stdout

## Usage Examples

### Example 1: Scan for Photos and Videos

An AI agent can ask the user what they want to scan, then call:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "photopuller_scan",
    "arguments": {
      "source_path": "C:\\",
      "scan_photos": true,
      "scan_videos": true,
      "scan_pdfs": false,
      "excluded_folders": ["C:\\Windows", "C:\\Program Files"]
    }
  }
}
```

### Example 2: Copy Files to Destination

After scanning, copy files to an organized destination:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "photopuller_copy_files",
    "arguments": {
      "destination": "D:\\Backup",
      "organize_method": "date",
      "dry_run": false
    }
  }
}
```

### Example 3: Dry Run (Preview)

Preview what would be copied without actually copying:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "photopuller_copy_files",
    "arguments": {
      "destination": "D:\\Backup",
      "organize_method": "date",
      "dry_run": true
    }
  }
}
```

## Protocol Details

### Request Format

All requests follow JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "id": <unique_id>,
  "method": "<method_name>",
  "params": { ... }
}
```

### Response Format

Successful responses:

```json
{
  "jsonrpc": "2.0",
  "id": <request_id>,
  "result": { ... }
}
```

Error responses:

```json
{
  "jsonrpc": "2.0",
  "id": <request_id>,
  "error": {
    "code": <error_code>,
    "message": "<error_message>"
  }
}
```

### Methods

#### `tools/list`

Lists all available tools with their schemas.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

**Response**: Returns tool definitions with input schemas.

#### `tools/call`

Calls a specific tool with arguments.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "photopuller_scan",
    "arguments": { ... }
  }
}
```

**Response**: Returns tool execution results.

## Testing the MCP Server

You can test the MCP server manually using a simple Python script:

```python
import json
import subprocess

# Start the server
process = subprocess.Popen(
    ["python", "mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Send a tools/list request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

# Read response
response = process.stdout.readline()
print(json.loads(response))

process.terminate()
```

## Security Considerations

⚠️ **Important Security Notes**:

1. **File System Access**: The MCP server has full access to the file system. Only connect it to trusted AI agents.

2. **Path Validation**: The server validates paths but always verify destination paths before copying to prevent accidental data loss.

3. **Dry Run Mode**: Always use `dry_run: true` first to preview operations before actually copying files.

4. **Permissions**: Ensure the Python process has appropriate permissions to read source files and write to destination directories.

## Troubleshooting

### Server Not Starting

- Verify Python is in your PATH
- Check that all PhotoPuller modules are accessible
- Ensure the working directory is correct

### Tools Not Appearing

- Check Claude Desktop logs for errors
- Verify the configuration file JSON is valid
- Restart Claude Desktop after configuration changes

### Permission Errors

- Ensure the Python process has read access to source paths
- Ensure the Python process has write access to destination paths
- On Windows, you may need to run with administrator privileges for system drives

## Advanced Configuration

### Custom Python Environment

If you're using a virtual environment:

```json
{
  "mcpServers": {
    "photopuller": {
      "command": "R:\\development\\photopuller\\venv\\Scripts\\python.exe",
      "args": [
        "R:\\development\\photopuller\\mcp_server.py"
      ],
      "cwd": "R:\\development\\photopuller"
    }
  }
}
```

### Logging

To enable debug logging, modify `mcp_server.py` to write to a log file:

```python
import logging

logging.basicConfig(
    filename='mcp_server.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Integration with Other AI Assistants

While this guide focuses on Claude Desktop, the MCP server can be integrated with any MCP-compatible client:

- **Custom Applications**: Use the MCP client library for your language
- **Web Services**: Wrap the stdio interface in an HTTP server
- **Other AI Platforms**: Check if they support MCP protocol

## Support

For issues or questions:
1. Check the PhotoPuller README.md for general application usage
2. Review the MCP server code in `mcp_server.py`
3. Test using the manual testing script above

