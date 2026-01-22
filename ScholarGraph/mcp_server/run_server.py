"""
Wrapper script to launch ScholarGraph MCP server with correct Python path.
"""
import sys
import os
import asyncio

# Add ScholarGraph to Python path
scholargraph_path = r"C:\projects\mkenteris01-code\ScholarGraph"
if scholargraph_path not in sys.path:
    sys.path.insert(0, scholargraph_path)

# Change to ScholarGraph directory
os.chdir(scholargraph_path)

# Import and run the server
from mcp_server.server import main

if __name__ == "__main__":
    asyncio.run(main())
