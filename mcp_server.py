"""
PhotoPuller MCP Server
Exposes PhotoPuller functionality to AI agents via Model Context Protocol
"""
import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path
from photopuller_core import PhotoPullerCore


class PhotoPullerMCPServer:
    """MCP Server for PhotoPuller that exposes tools to AI agents"""
    
    def __init__(self):
        self.core = PhotoPullerCore()
        self.scan_results = []
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                result = self.call_tool(params.get("name"), params.get("arguments", {}))
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools"""
        return {
            "tools": [
                {
                    "name": "photopuller_scan",
                    "description": "Scan a drive or directory for photos, videos, and PDFs",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "source_path": {
                                "type": "string",
                                "description": "Path to scan (e.g., 'C:\\' or 'D:\\Photos')"
                            },
                            "scan_photos": {
                                "type": "boolean",
                                "description": "Include photos in scan",
                                "default": True
                            },
                            "scan_videos": {
                                "type": "boolean",
                                "description": "Include videos in scan",
                                "default": True
                            },
                            "scan_pdfs": {
                                "type": "boolean",
                                "description": "Include PDFs in scan",
                                "default": True
                            },
                            "excluded_folders": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of folder paths to exclude from scan",
                                "default": []
                            }
                        },
                        "required": ["source_path"]
                    }
                },
                {
                    "name": "photopuller_get_scan_stats",
                    "description": "Get statistics about the last scan operation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "photopuller_copy_files",
                    "description": "Copy scanned files to a destination directory with organization",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "destination": {
                                "type": "string",
                                "description": "Destination directory path"
                            },
                            "organize_method": {
                                "type": "string",
                                "enum": ["date", "source"],
                                "description": "Organization method: 'date' (Year/Month) or 'source' (by drive)",
                                "default": "date"
                            },
                            "dry_run": {
                                "type": "boolean",
                                "description": "If true, simulate copying without actually copying files",
                                "default": False
                            }
                        },
                        "required": ["destination"]
                    }
                },
                {
                    "name": "photopuller_get_copy_stats",
                    "description": "Get statistics about the last copy operation",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                },
                {
                    "name": "photopuller_add_exclusion",
                    "description": "Add a folder to the exclusion list",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "Path to folder to exclude"
                            }
                        },
                        "required": ["folder_path"]
                    }
                },
                {
                    "name": "photopuller_remove_exclusion",
                    "description": "Remove a folder from the exclusion list",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "Path to folder to remove from exclusions"
                            }
                        },
                        "required": ["folder_path"]
                    }
                },
                {
                    "name": "photopuller_clear_exclusions",
                    "description": "Clear all excluded folders",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ]
        }
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with given arguments"""
        if tool_name == "photopuller_scan":
            return self._scan(arguments)
        elif tool_name == "photopuller_get_scan_stats":
            return self._get_scan_stats()
        elif tool_name == "photopuller_copy_files":
            return self._copy_files(arguments)
        elif tool_name == "photopuller_get_copy_stats":
            return self._get_copy_stats()
        elif tool_name == "photopuller_add_exclusion":
            return self._add_exclusion(arguments)
        elif tool_name == "photopuller_remove_exclusion":
            return self._remove_exclusion(arguments)
        elif tool_name == "photopuller_clear_exclusions":
            return self._clear_exclusions()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def _scan(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for files"""
        source_path = args["source_path"]
        scan_photos = args.get("scan_photos", True)
        scan_videos = args.get("scan_videos", True)
        scan_pdfs = args.get("scan_pdfs", True)
        excluded_folders = args.get("excluded_folders", [])
        
        # Collect progress updates
        progress_updates = []
        
        def progress_callback(current_path, stats):
            progress_updates.append({
                "current_path": str(current_path),
                "stats": stats.copy()
            })
        
        try:
            found_files = self.core.scan(
                source_path,
                scan_photos=scan_photos,
                scan_videos=scan_videos,
                scan_pdfs=scan_pdfs,
                excluded_folders=excluded_folders,
                progress_callback=progress_callback
            )
            
            stats = self.core.get_scan_stats()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "files_found": len(found_files),
                            "stats": stats,
                            "sample_files": [str(f) for f in found_files[:10]]  # First 10 files as sample
                        }, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e)
                        }, indent=2)
                    }
                ],
                "isError": True
            }
    
    def _get_scan_stats(self) -> Dict[str, Any]:
        """Get scan statistics"""
        try:
            stats = self.core.get_scan_stats()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(stats, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e)
                        }, indent=2)
                    }
                ],
                "isError": True
            }
    
    def _copy_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Copy files to destination"""
        destination = args["destination"]
        organize_method = args.get("organize_method", "date")
        dry_run = args.get("dry_run", False)
        
        # Collect progress updates
        progress_updates = []
        
        def progress_callback(current_file, copy_stats, copy_status=None):
            progress_updates.append({
                "current_file": str(current_file),
                "stats": copy_stats.copy(),
                "status": copy_status
            })
        
        try:
            results = self.core.copy_files(
                destination,
                organize_method=organize_method,
                dry_run=dry_run,
                progress_callback=progress_callback
            )
            
            copy_stats = self.core.get_copy_stats()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "dry_run": dry_run,
                            "files_processed": len(results),
                            "copy_stats": copy_stats,
                            "sample_results": results[:10]  # First 10 results as sample
                        }, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e)
                        }, indent=2)
                    }
                ],
                "isError": True
            }
    
    def _get_copy_stats(self) -> Dict[str, Any]:
        """Get copy statistics"""
        try:
            stats = self.core.get_copy_stats()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(stats, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e)
                        }, indent=2)
                    }
                ],
                "isError": True
            }
    
    def _add_exclusion(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add folder to exclusion list"""
        try:
            folder_path = args["folder_path"]
            self.core.add_excluded_folder(folder_path)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "message": f"Added exclusion: {folder_path}",
                            "excluded_folders": [str(f) for f in sorted(self.core.excluded_folders)]
                        }, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e)
                        }, indent=2)
                    }
                ],
                "isError": True
            }
    
    def _remove_exclusion(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove folder from exclusion list"""
        try:
            folder_path = args["folder_path"]
            self.core.remove_excluded_folder(folder_path)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "message": f"Removed exclusion: {folder_path}",
                            "excluded_folders": [str(f) for f in sorted(self.core.excluded_folders)]
                        }, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e)
                        }, indent=2)
                    }
                ],
                "isError": True
            }
    
    def _clear_exclusions(self) -> Dict[str, Any]:
        """Clear all exclusions"""
        try:
            self.core.clear_excluded_folders()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "message": "All exclusions cleared"
                        }, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "error",
                            "error": str(e)
                        }, indent=2)
                    }
                ],
                "isError": True
            }


def main():
    """Main entry point for MCP server - communicates via stdio"""
    server = PhotoPullerMCPServer()
    
    # Read from stdin, write to stdout
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            # Invalid JSON, skip
            continue
        except Exception as e:
            # Send error response
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()

