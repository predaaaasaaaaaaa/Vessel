import os
import pytest
from pydantic import BaseModel
from vessel.mcp.server import VesselServer

@pytest.mark.asyncio
async def test_vessel_server_loading_and_execution(tmp_path):
    """Test that the VesselServer can load skills from a directory and execute them."""
    
    # 1. Create a dummy Vessel in the temporary directory
    vessel_file = tmp_path / "math_vessel.py"
    vessel_file.write_text('''
from pydantic import BaseModel
from vessel.core.base import BaseVessel

class MathInput(BaseModel):
    val: int

class MathOutput(BaseModel):
    result: int

class MathVessel(BaseVessel[MathInput, MathOutput]):
    """Multiplies a number by 2."""
    def execute(self, inputs: MathInput) -> MathOutput:
        return MathOutput(result=inputs.val * 2)
''')

    # 2. Initialize the Server and load the directory
    server = VesselServer()
    server.load_vessels_from_directory(str(tmp_path))
    
    # 3. Verify the tool was dynamically loaded and registered
    tools = await server.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "MathVessel"
    assert "Multiplies a number by 2" in tools[0].description
    
    # 4. Simulate the Agent executing the tool
    result_content = await server.call_tool("MathVessel", {"val": 21})
    
    # 5. Verify the tool returned the correctly formatted output
    assert len(result_content) == 1
    assert result_content[0].type == "text"
    assert "42" in result_content[0].text
