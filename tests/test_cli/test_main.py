import os
from click.testing import CliRunner
from vessel.cli.main import cli

def test_vessel_create_wizard(tmp_path):
    """
    Test that the interactive wizard generates a valid Vessel Python template
    AND the Fat Skill.md documentation for the Agent.
    """
    runner = CliRunner()
    
    # We change the working directory to a temporary path so we don't litter the repo
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # We simulate the user typing answers to the prompts:
        # 1. "LeadGenVessel" (The name of the skill)
        # 2. "Searches the web for SaaS leads and verifies their emails." (The description)
        result = runner.invoke(cli, ["create"], input="LeadGenVessel\nSearches the web for SaaS leads and verifies their emails.\n")
        
        # 1. Verify the command ran successfully
        assert result.exit_code == 0
        assert "Welcome to the Vessel Creator Wizard!" in result.output
        assert "Successfully created leadgenvessel.py!" in result.output
        assert "Successfully created LeadGenVessel_SKILL.md!" in result.output
        
        # 2. Verify the files were actually created
        assert os.path.exists("leadgenvessel.py")
        assert os.path.exists("LeadGenVessel_SKILL.md")
        
        # 3. Verify the generated Python code contains the correct structure
        with open("leadgenvessel.py", "r") as f:
            content = f.read()
            assert "class LeadGenVesselInput(BaseModel):" in content
            assert "class LeadGenVesselOutput(BaseModel):" in content
            assert "class LeadGenVessel(BaseVessel[" in content
            assert '"""\n    Searches the web for SaaS leads and verifies their emails.\n    """' in content

        # 4. Verify the generated Markdown file is ready for the Agent
        with open("LeadGenVessel_SKILL.md", "r") as f:
            md_content = f.read()
            assert "# Skill: LeadGenVessel" in md_content
            assert "Searches the web for SaaS leads and verifies their emails." in md_content
            assert "## Deterministic Execution" in md_content
            assert "Do not attempt to write custom scripts to perform this task." in md_content
