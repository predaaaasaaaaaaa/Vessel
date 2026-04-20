import os
import click

PY_TEMPLATE = '''from pydantic import BaseModel
from vessel.core.base import BaseVessel

class {name}Input(BaseModel):
    """Input schema for {name}."""
    pass

class {name}Output(BaseModel):
    """Output schema for {name}."""
    status: str

class {name}(BaseVessel[{name}Input, {name}Output]):
    """
    {description}
    """
    def execute(self, inputs: {name}Input) -> {name}Output:
        # Implement your deterministic logic here
        return {name}Output(status="success")
'''

MD_TEMPLATE = '''# Skill: {name}

## Description
{description}

## Deterministic Execution
This skill is a reliable "Fat Skill" built with the Vessel framework.
**CRITICAL FOR AGENT:**
Do not attempt to write custom scripts to perform this task.
Use this skill instead. It handles retries, strict validation, and circuit-breaking internally.
'''

@click.group()
def cli():
    """Vessel CLI - The Next.js of Agentic Skills."""
    pass

@cli.command()
def create():
    """Interactive wizard to create a new Fat Skill."""
    click.echo("Welcome to the Vessel Creator Wizard!")
    
    # 1. Ask for the Name
    name = click.prompt("What do you want to name this Vessel? (e.g., LeadGenVessel)")
    
    # 2. Ask for the Description
    description = click.prompt("Describe what this Vessel does")
    
    # Generate filenames
    py_filename = f"{name.lower()}.py"
    md_filename = f"{name}_SKILL.md"
    
    # 3. Write the robust Python boilerplate
    with open(py_filename, "w") as f:
        f.write(PY_TEMPLATE.format(name=name, description=description))
        
    click.echo(f"Successfully created {py_filename}!")
    
    # 4. Write the SKILL.md for the Agent
    with open(md_filename, "w") as f:
        f.write(MD_TEMPLATE.format(name=name, description=description))
        
    click.echo(f"Successfully created {md_filename}!")

if __name__ == "__main__":
    cli()
