import pytest
from pydantic import BaseModel, Field
from mcp.types import Tool

from vessel.core.base import BaseVessel
from vessel.mcp.adapter import create_mcp_tool

class WeatherInput(BaseModel):
    location: str = Field(..., description="The city and state, e.g., San Francisco, CA")
    unit: str = Field(default="celsius", description="Temperature unit (celsius or fahrenheit)")

class WeatherOutput(BaseModel):
    temperature: float
    description: str

class WeatherVessel(BaseVessel[WeatherInput, WeatherOutput]):
    """
    Get the current weather for a given location.
    This tool provides real-time meteorological data.
    """
    def execute(self, inputs: WeatherInput) -> WeatherOutput:
        return WeatherOutput(temperature=22.5, description="Sunny")

def test_vessel_to_mcp_tool_conversion():
    """Test that a BaseVessel is correctly converted to an MCP Tool type."""
    vessel = WeatherVessel()
    mcp_tool = create_mcp_tool(vessel)
    
    # 1. Type Check
    assert isinstance(mcp_tool, Tool)
    
    # 2. Metadata Extraction (Name and Description)
    assert mcp_tool.name == "WeatherVessel"
    
    # It should extract the docstring for the LLM's understanding
    assert "Get the current weather for a given location." in mcp_tool.description
    
    # 3. JSON Schema Extraction (The magic part)
    schema = mcp_tool.inputSchema
    assert schema["type"] == "object"
    assert "location" in schema["properties"]
    assert "unit" in schema["properties"]
    
    # It must carry over the Pydantic field descriptions so the LLM knows what to provide
    assert schema["properties"]["location"]["description"] == "The city and state, e.g., San Francisco, CA"
    
    # It must know which fields are mandatory
    assert "location" in schema["required"]
