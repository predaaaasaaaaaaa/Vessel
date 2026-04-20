import os
import sys
import json
import click
import inspect
import importlib.util
from pydantic import ValidationError
from vessel.core.base import BaseVessel

PY_TEMPLATE = '''import sys
import json
from pydantic import BaseModel
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {{sys.argv[0]}} '<json_payload>'", file=sys.stderr)
        sys.exit(1)
        
    try:
        payload = json.loads(sys.argv[1])
        vessel = {name}()
        result = vessel.run(payload)
        print(result.model_dump_json())
    except Exception as e:
        print(f"Fat Skill Execution Failed: {{e}}", file=sys.stderr)
        sys.exit(1)
'''

MD_TEMPLATE = '''# Skill: {name}

## Description
{description}

## Agent Instructions: How to Use This Skill
This is a deterministic "Fat Skill". 
**CRITICAL:** Do NOT attempt to write custom python scripts or use raw APIs to perform this task. Do NOT worry about rate limits, retries, or complex error handling. This Skill handles everything internally to guarantee 100% reliability.

### Execution Protocol
To execute this skill, use your terminal/shell capability to run the accompanying Python script. Pass the input arguments as a strict JSON string.

**Command Format:**
```bash
python {py_filename} '<json_payload>'
```

**Example:**
```bash
python {py_filename} '{{"target": "example"}}'
```

### Outputs
If successful, the script will print a validated JSON object to `stdout`.
If it fails, it will print the error to `stderr` and return a non-zero exit code. Do not attempt to fix the Python code if it fails; adjust your JSON payload according to the schema.
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
        f.write(MD_TEMPLATE.format(name=name, description=description, py_filename=py_filename))
        
    click.echo(f"Successfully created {md_filename}!")

@cli.command()
@click.argument("filepath")
@click.argument("payload", required=False)
def test(filepath, payload):
    """Dynamically load and test a Vessel file."""
    if not os.path.exists(filepath):
        click.echo(f"Error: File {filepath} not found.", err=True)
        sys.exit(1)
        
    if not payload:
        payload = click.prompt("Enter JSON payload for the Vessel")
        
    try:
        parsed_payload = json.loads(payload)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON payload. {e}", err=True)
        sys.exit(1)

    # Dynamically load the module
    module_name = "dynamic_vessel_module"
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None or spec.loader is None:
        click.echo(f"Error: Could not load module from {filepath}", err=True)
        sys.exit(1)
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    
    # Add the directory of the filepath to sys.path so relative imports in the vessel work
    sys.path.insert(0, os.path.dirname(os.path.abspath(filepath)))
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        click.echo(f"Error executing module: {e}", err=True)
        sys.exit(1)
        
    # Find the BaseVessel subclass
    vessel_class = None
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseVessel) and obj is not BaseVessel:
            vessel_class = obj
            break
            
    if not vessel_class:
        click.echo(f"Error: No BaseVessel subclass found in {filepath}", err=True)
        sys.exit(1)
        
    click.echo(f"Executing {vessel_class.__name__} from {filepath}...")
    vessel_instance = vessel_class()
    
    try:
        result = vessel_instance.run(parsed_payload)
        click.echo("\n--- RESULT ---")
        click.echo(result.model_dump_json(indent=2))
    except ValidationError as e:
        click.echo(f"\n--- VALIDATION ERROR ---\n{e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n--- EXECUTION ERROR ---\n{e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument("directory", default=".")
def serve(directory):
    """Start the MCP server over stdio, exposing all Vessels in the directory."""
    import asyncio
    from vessel.mcp.server import VesselServer
    
    server = VesselServer()
    try:
        server.load_vessels_from_directory(directory)
    except Exception as e:
        click.echo(f"Error loading vessels: {e}", err=True)
        sys.exit(1)
        
    click.echo(f"Starting Vessel MCP Server on stdio...", err=True)
    asyncio.run(server.run_stdio())

if __name__ == "__main__":
    cli()
