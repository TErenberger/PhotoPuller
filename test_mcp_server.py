"""
Simple test script for PhotoPuller MCP Server
Tests basic functionality without requiring a full MCP client
"""
import json
import subprocess
import sys
from pathlib import Path


def test_mcp_server():
    """Test the MCP server with basic requests"""
    
    # Get the path to mcp_server.py
    script_path = Path(__file__).parent / "mcp_server.py"
    
    print("Starting MCP server test...")
    print(f"Server script: {script_path}")
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
    
    def send_request(method, params=None, request_id=1):
        """Send a JSON-RPC request and get response"""
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
    
    # Test 1: List tools
    print("Test 1: Listing available tools...")
    response = send_request("tools/list", request_id=1)
    if response and "result" in response:
        tools = response["result"].get("tools", [])
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
    else:
        print(f"✗ Failed: {response}")
        process.terminate()
        return False
    print()
    
    # Test 2: Get scan stats (should work even without a scan)
    print("Test 2: Getting scan stats (before scan)...")
    response = send_request("tools/call", {
        "name": "photopuller_get_scan_stats",
        "arguments": {}
    }, request_id=2)
    if response and "result" in response:
        print("✓ Get scan stats succeeded")
        content = response["result"].get("content", [])
        if content:
            print(f"  Response: {content[0].get('text', '')[:100]}...")
    else:
        print(f"✗ Failed: {response}")
    print()
    
    # Test 3: Clear exclusions
    print("Test 3: Clearing exclusions...")
    response = send_request("tools/call", {
        "name": "photopuller_clear_exclusions",
        "arguments": {}
    }, request_id=3)
    if response and "result" in response:
        print("✓ Clear exclusions succeeded")
    else:
        print(f"✗ Failed: {response}")
    print()
    
    # Test 4: Invalid method
    print("Test 4: Testing invalid method...")
    response = send_request("invalid/method", request_id=4)
    if response and "error" in response:
        print(f"✓ Correctly returned error: {response['error']['message']}")
    else:
        print(f"✗ Should have returned error: {response}")
    print()
    
    # Cleanup
    process.terminate()
    process.wait()
    
    print("All tests completed!")
    return True


if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)

