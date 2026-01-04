"""
Test script for PhotoPuller MCP Server - Dry Run Test
Tests the full workflow: scan D:\ drive and perform a dry run copy
"""
import json
import subprocess
import sys
from pathlib import Path


def test_mcp_dry_run():
    """Test the MCP server with a scan and dry run on D:\\"""
    
    # Get the path to mcp_server.py
    script_path = Path(__file__).parent / "mcp_server.py"
    
    print("=" * 70)
    print("PhotoPuller MCP Server - Dry Run Test")
    print("=" * 70)
    print(f"Server script: {script_path}")
    print(f"Source drive: D:\\")
    print(f"Mode: DRY RUN (no files will be copied)")
    print()
    
    # Start the server process
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        return False
    
    request_id = 0
    
    def send_request(method, params=None):
        """Send a JSON-RPC request and get response"""
        nonlocal request_id
        request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params:
            request["params"] = params
        
        try:
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Read response (blocking)
            response_line = process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            return None
        except Exception as e:
            print(f"Error sending request: {e}")
            return None
    
    try:
        # Step 1: List tools
        print("Step 1: Listing available tools...")
        response = send_request("tools/list")
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"[OK] Found {len(tools)} tools")
            print()
        else:
            print(f"[ERROR] Failed to list tools: {response}")
            return False
        
        # Step 2: Scan D:\ drive
        print("Step 2: Scanning D:\\ drive for photos, videos, and PDFs...")
        print("(This may take a while depending on the size of the drive)")
        print()
        
        scan_params = {
            "name": "photopuller_scan",
            "arguments": {
                "source_path": "D:\\",
                "scan_photos": True,
                "scan_videos": True,
                "scan_pdfs": True,
                "excluded_folders": []
            }
        }
        
        response = send_request("tools/call", scan_params)
        if response and "result" in response:
            result = response["result"]
            content = result.get("content", [])
            if content:
                try:
                    scan_data = json.loads(content[0].get("text", "{}"))
                    if scan_data.get("status") == "success":
                        stats = scan_data.get("stats", {})
                        files_found = scan_data.get("files_found", 0)
                        print(f"[OK] Scan completed successfully!")
                        print(f"  Files found: {files_found}")
                        print(f"  Photos: {stats.get('photos', 0)}")
                        print(f"  Videos: {stats.get('videos', 0)}")
                        print(f"  PDFs: {stats.get('pdfs', 0)}")
                        print(f"  Total size: {stats.get('total_size_gb', 0):.2f} GB")
                        print(f"  Excluded: {stats.get('excluded_count', 0)}")
                        print()
                    else:
                        print(f"[ERROR] Scan failed: {scan_data.get('error', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    print(f"[ERROR] Failed to parse scan response")
                    return False
        else:
            error = response.get("error", {}) if response else {}
            print(f"[ERROR] Scan request failed: {error.get('message', 'Unknown error')}")
            if response:
                print(f"  Full response: {json.dumps(response, indent=2)}")
            return False
        
        # Step 3: Get scan stats
        print("Step 3: Getting detailed scan statistics...")
        stats_params = {
            "name": "photopuller_get_scan_stats",
            "arguments": {}
        }
        
        response = send_request("tools/call", stats_params)
        if response and "result" in response:
            result = response["result"]
            content = result.get("content", [])
            if content:
                try:
                    stats = json.loads(content[0].get("text", "{}"))
                    print("[OK] Scan statistics retrieved:")
                    print(json.dumps(stats, indent=2))
                    print()
                except json.JSONDecodeError:
                    print("[ERROR] Failed to parse stats response")
        else:
            print("[WARNING] Could not retrieve detailed stats")
        
        # Step 4: Dry run copy (simulate copying to a temporary destination)
        print("Step 4: Performing DRY RUN copy operation...")
        print("(No files will actually be copied)")
        print()
        
        # For dry run, we'll use a dummy destination path since no files will be copied
        copy_params = {
            "name": "photopuller_copy_files",
            "arguments": {
                "destination": "D:\\PhotoPuller_Backup_Test",
                "organize_method": "date",
                "dry_run": True
            }
        }
        
        response = send_request("tools/call", copy_params)
        if response and "result" in response:
            result = response["result"]
            content = result.get("content", [])
            if content:
                try:
                    copy_data = json.loads(content[0].get("text", "{}"))
                    if copy_data.get("status") == "success":
                        copy_stats = copy_data.get("copy_stats", {})
                        files_processed = copy_data.get("files_processed", 0)
                        print(f"[OK] Dry run completed successfully!")
                        print(f"  Files that would be processed: {files_processed}")
                        if copy_stats:
                            print(f"  Would copy: {copy_stats.get('copied', 0)}")
                            print(f"  Would skip: {copy_stats.get('skipped', 0)}")
                            print(f"  Errors: {copy_stats.get('errors', 0)}")
                            print(f"  Duplicates: {copy_stats.get('duplicates', 0)}")
                        print()
                    else:
                        print(f"[ERROR] Dry run failed: {copy_data.get('error', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    print(f"[ERROR] Failed to parse copy response")
                    return False
        else:
            error = response.get("error", {}) if response else {}
            print(f"[ERROR] Dry run request failed: {error.get('message', 'Unknown error')}")
            if response:
                print(f"  Full response: {json.dumps(response, indent=2)}")
            return False
        
        # Step 5: Get copy stats
        print("Step 5: Getting copy operation statistics...")
        copy_stats_params = {
            "name": "photopuller_get_copy_stats",
            "arguments": {}
        }
        
        response = send_request("tools/call", copy_stats_params)
        if response and "result" in response:
            result = response["result"]
            content = result.get("content", [])
            if content:
                try:
                    stats = json.loads(content[0].get("text", "{}"))
                    print("[OK] Copy statistics retrieved:")
                    print(json.dumps(stats, indent=2))
                    print()
                except json.JSONDecodeError:
                    print("[ERROR] Failed to parse copy stats response")
        else:
            print("[WARNING] Could not retrieve detailed copy stats")
        
        print("=" * 70)
        print("[OK] All tests completed successfully!")
        print("=" * 70)
        print()
        print("Summary:")
        print("- MCP server is working correctly")
        print("- Scan operation completed successfully")
        print("- Dry run operation completed successfully")
        print("- No files were actually copied (dry run mode)")
        print()
        
        return True
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return False
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass


if __name__ == "__main__":
    success = test_mcp_dry_run()
    sys.exit(0 if success else 1)

