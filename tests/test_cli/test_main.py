import os
import json
from click.testing import CliRunner
from vessel.cli.main import cli

def test_vessel_create_wizard(tmp_path):
    """
    Test that the interactive wizard generates a valid Vessel Python template
    AND the Fat Skill.md documentation for the Agent.
    """
    runner = CliRunner()
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["create"], input="LeadGenVessel\nSearches the web for SaaS leads and verifies their emails.\n")
        
        assert result.exit_code == 0
        assert "Welcome to the Vessel Creator Wizard!" in result.output
        assert "Successfully created leadgenvessel.py!" in result.output
        assert "Successfully created LeadGenVessel_SKILL.md!" in result.output
        
        assert os.path.exists("leadgenvessel.py")
        assert os.path.exists("LeadGenVessel_SKILL.md")
        
        with open("leadgenvessel.py", "r") as f:
            content = f.read()
            assert "class LeadGenVesselInput(BaseModel):" in content
            assert "class LeadGenVesselOutput(BaseModel):" in content
            assert "class LeadGenVessel(BaseVessel[" in content
            assert '"""\n    Searches the web for SaaS leads and verifies their emails.\n    """' in content

        with open("LeadGenVessel_SKILL.md", "r") as f:
            md_content = f.read()
            assert "# Skill: LeadGenVessel" in md_content
            assert "Searches the web for SaaS leads and verifies their emails." in md_content
            assert "## Deterministic Execution" in md_content
            assert "Do not attempt to write custom scripts to perform this task." in md_content

def test_vessel_test_command(tmp_path):
    """Test that the CLI can dynamically load and execute a Vessel file."""
    runner = CliRunner()
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # 1. Create a dummy Vessel
        with open("dummyvessel.py", "w") as f:
            f.write('''
from pydantic import BaseModel
from vessel.core.base import BaseVessel

class DummyInput(BaseModel):
    target: str

class DummyOutput(BaseModel):
    result: str

class DummyVessel(BaseVessel[DummyInput, DummyOutput]):
    def execute(self, inputs: DummyInput) -> DummyOutput:
        return DummyOutput(result=f"Hello {inputs.target}")
''')
        
        # 2. Run `vessel test` with a JSON payload
        result = runner.invoke(cli, ["test", "dummyvessel.py", '{"target": "World"}'])
        
        # 3. Verify it loaded, ran, and output the correct result
        assert result.exit_code == 0
        assert "Executing DummyVessel" in result.output
        assert "Hello World" in result.output
