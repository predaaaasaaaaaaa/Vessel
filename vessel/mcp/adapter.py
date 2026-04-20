import inspect
from mcp.types import Tool
from pydantic import BaseModel
from typing import Type

from vessel.core.base import BaseVessel

def extract_vessel_description(vessel: BaseVessel) -> str:
    """
    Extracts and cleans the docstring from a Vessel to use as the MCP Tool description.
    """
    doc = inspect.getdoc(vessel)
    if doc:
        # Return a cleaned, stripped version of the docstring
        return inspect.cleandoc(doc)
    return f"A deterministic tool: {vessel.__class__.__name__}"

def create_mcp_tool(vessel: BaseVessel) -> Tool:
    """
    Dynamically introspects a BaseVessel and returns a fully compliant MCP Tool object.
    
    This function bridges the gap between our robust 'Fat Skill' and the standard
    Model Context Protocol used by LLMs.
    """
    # 1. Get the Pydantic input model bound to this Vessel
    input_model: Type[BaseModel] = vessel._get_input_model()
    
    # 2. Extract the Name and Description
    name = vessel.__class__.__name__
    description = extract_vessel_description(vessel)
    
    # 3. Generate the JSON Schema directly from Pydantic
    # Pydantic's schema generation is perfectly aligned with what MCP needs
    schema = input_model.model_json_schema()
    
    # 4. Construct the MCP Tool
    return Tool(
        name=name,
        description=description,
        inputSchema=schema
    )
