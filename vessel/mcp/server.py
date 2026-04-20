import os
import sys
import inspect
import importlib.util
from typing import List, Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import ValidationError
from loguru import logger

from vessel.core.base import BaseVessel
from vessel.mcp.adapter import create_mcp_tool

class VesselServer:
    """
    The bridge between our deterministically executing Fat Skills and the Agent.
    Scans a directory for Vessels, translates them, and exposes them via MCP.
    """
    def __init__(self, name: str = "vessel-mcp-server"):
        self.server = Server(name)
        self.vessels: Dict[str, BaseVessel] = {}
        self.tools: List[Tool] = []
        
        # Register the core MCP handlers natively
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    def load_vessels_from_directory(self, directory: str):
        """
        Dynamically loads any python file in the directory that contains a BaseVessel subclass.
        """
        if not os.path.exists(directory):
            logger.error(f"Directory {directory} not found.")
            raise ValueError(f"Directory {directory} does not exist.")
            
        sys.path.insert(0, os.path.abspath(directory))
        logger.info(f"Scanning directory '{directory}' for Fat Skills...")
        
        for filename in os.listdir(directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(directory, filename)
                module_name = f"vessel_dynamic_{filename[:-3]}"
                
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(module)
                        
                        # Find any class that inherits from BaseVessel
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseVessel) and obj is not BaseVessel:
                                vessel_instance = obj()
                                
                                # Use our Adapter to convert it to an MCP Tool
                                mcp_tool = create_mcp_tool(vessel_instance)
                                
                                self.vessels[mcp_tool.name] = vessel_instance
                                self.tools.append(mcp_tool)
                                logger.success(f"Registered Tool: {mcp_tool.name} from {filename}")
                                
                    except Exception as e:
                        logger.warning(f"Skipping {filename} due to load error: {e}")

    async def list_tools(self) -> List[Tool]:
        """MCP endpoint: Return the list of available tools to the Agent."""
        return self.tools

    async def call_tool(self, name: str, arguments: dict) -> list[Any]:
        """MCP endpoint: Execute a specific tool deterministically."""
        if name not in self.vessels:
            logger.error(f"Agent requested unknown tool: {name}")
            raise ValueError(f"Unknown tool: {name}")
            
        vessel = self.vessels[name]
        logger.info(f"Agent executing {name}...")
        
        try:
            # We use the native .run() method which handles validation and retries
            result = vessel.run(arguments)
            
            # The Agent receives a clean, stringified JSON payload
            return [TextContent(type="text", text=result.model_dump_json())]
            
        except ValidationError as e:
            # The Agent fed us bad data. Return it nicely so it can learn and retry.
            logger.error(f"Validation Error in {name}: {e}")
            return [TextContent(type="text", text=f"Validation Error: {e}")]
        except Exception as e:
            logger.error(f"Execution Error in {name}: {e}")
            return [TextContent(type="text", text=f"Execution Error: {e}")]

    async def run_stdio(self):
        """Starts the server using standard input/output (the default MCP protocol for local agents)."""
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
