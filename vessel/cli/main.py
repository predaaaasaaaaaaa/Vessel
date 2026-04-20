import os
import sys
import json
import click
import inspect
import importlib.util
from pydantic import ValidationError
from vessel.core.base import BaseVessel

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.prompt import Prompt

# The Monochromatic Purple Theme Hex Palette
PRIMARY = "#9d4edd"    # Deep Electric Purple (Logos, Borders)
SECONDARY = "#c77dff"  # Medium Amethyst (Headers, Subtitles)
PROMPT = "#e0aaff"     # Light Lavender (Questions, Prompts)
MUTED = "#5a189a"      # Dark Violet (Secondary Text, Dividers)

console = Console()

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

def print_logo():
    logo_art = """
 ██╗   ██╗ ███████╗ ███████╗ ███████╗ ███████╗ ██╗     
 ██║   ██║ ██╔════╝ ██╔════╝ ██╔════╝ ██╔════╝ ██║     
 ██║   ██║ █████╗   ███████╗ ███████╗ █████╗   ██║     
 ╚██╗ ██╔╝ ██╔══╝   ╚════██║ ╚════██║ ██╔══╝   ██║     
  ╚████╔╝  ███████╗ ███████║ ███████║ ███████╗ ███████╗
   ╚═══╝   ╚══════╝ ╚══════╝ ╚══════╝ ╚══════╝ ╚══════╝
"""
    console.print(Text(logo_art, style=f"bold {PRIMARY}"))
    console.print(f"[{SECONDARY}]   The Next.js of Agentic Skills[/{SECONDARY}]\n")

@click.group()
def cli():
    """Vessel CLI - The Next.js of Agentic Skills."""
    pass

@cli.command()
def create():
    """Interactive wizard to create a new Fat Skill."""
    print_logo()
    
    # 1. Ask for the Name
    console.print(f"[{PROMPT}]?[/{PROMPT}] [{SECONDARY}]What do you want to name this Vessel? (e.g., LeadGenVessel)[/{SECONDARY}]")
    name = Prompt.ask(f"[{MUTED}]❯[/{MUTED}] ")
    console.print("")
    
    # 2. Ask for the Description
    console.print(f"[{PROMPT}]?[/{PROMPT}] [{SECONDARY}]Describe what this Vessel does[/{SECONDARY}]")
    description = Prompt.ask(f"[{MUTED}]❯[/{MUTED}] ")
    console.print("")
    
    # Generate filenames
    py_filename = f"{name.lower()}.py"
    md_filename = f"{name}_SKILL.md"
    
    # 3. Write the robust Python boilerplate
    with open(py_filename, "w") as f:
        f.write(PY_TEMPLATE.format(name=name, description=description))
        
    console.print(f"[{PRIMARY}]✦[/{PRIMARY}] [{PROMPT}]Created {py_filename}[/{PROMPT}]")
    
    # 4. Write the SKILL.md for the Agent
    with open(md_filename, "w") as f:
        f.write(MD_TEMPLATE.format(name=name, description=description, py_filename=py_filename))
        
    console.print(f"[{PRIMARY}]✦[/{PRIMARY}] [{PROMPT}]Created {md_filename}[/{PROMPT}]")
    console.print(f"\n[{SECONDARY}]Vessel ready for Agentic deployment.[/{SECONDARY}]\n")

@cli.command()
@click.argument("filepath")
@click.argument("payload", required=False)
def test(filepath, payload):
    """Dynamically load and test a Vessel file."""
    if not os.path.exists(filepath):
        console.print(f"[{PRIMARY}]✖[/{PRIMARY}] [{PROMPT}]Error: File {filepath} not found.[/{PROMPT}]")
        sys.exit(1)
        
    if not payload:
        console.print(f"[{PROMPT}]?[/{PROMPT}] [{SECONDARY}]Enter JSON payload for the Vessel[/{SECONDARY}]")
        payload = Prompt.ask(f"[{MUTED}]❯[/{MUTED}] ")
        console.print("")
        
    try:
        parsed_payload = json.loads(payload)
    except json.JSONDecodeError as e:
        console.print(f"[{PRIMARY}]✖[/{PRIMARY}] [{PROMPT}]Error: Invalid JSON payload. {e}[/{PROMPT}]")
        sys.exit(1)

    # Dynamically load the module
    module_name = "dynamic_vessel_module"
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None or spec.loader is None:
        console.print(f"[{PRIMARY}]✖[/{PRIMARY}] [{PROMPT}]Error: Could not load module from {filepath}[/{PROMPT}]")
        sys.exit(1)
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    
    sys.path.insert(0, os.path.dirname(os.path.abspath(filepath)))
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        console.print(f"[{PRIMARY}]✖[/{PRIMARY}] [{PROMPT}]Error executing module: {e}[/{PROMPT}]")
        sys.exit(1)
        
    vessel_class = None
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseVessel) and obj is not BaseVessel:
            vessel_class = obj
            break
            
    if not vessel_class:
        console.print(f"[{PRIMARY}]✖[/{PRIMARY}] [{PROMPT}]Error: No BaseVessel subclass found in {filepath}[/{PROMPT}]")
        sys.exit(1)
        
    vessel_instance = vessel_class()
    
    try:
        result = vessel_instance.run(parsed_payload)
        json_result = result.model_dump_json(indent=2)
        syntax = Syntax(json_result, "json", theme="dracula", background_color="default")
        result_panel = Panel(
            syntax, 
            title=f"[{SECONDARY}]Execution Result ({os.path.basename(filepath)})[/{SECONDARY}]", 
            title_align="left",
            border_style=MUTED, 
            padding=(1, 2)
        )
        console.print(result_panel)
    except ValidationError as e:
        console.print(f"\n[{PRIMARY}]✖ VALIDATION ERROR[/{PRIMARY}]\n[{PROMPT}]{e}[/{PROMPT}]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[{PRIMARY}]✖ EXECUTION ERROR[/{PRIMARY}]\n[{PROMPT}]{e}[/{PROMPT}]")
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
        console.print(f"[{PRIMARY}]✖[/{PRIMARY}] [{PROMPT}]Error loading vessels: {e}[/{PROMPT}]")
        sys.exit(1)
        
    console.print(f"[{PRIMARY}]✦[/{PRIMARY}] [{PROMPT}]Starting Vessel MCP Server on stdio...[/{PROMPT}]")
    asyncio.run(server.run_stdio())

if __name__ == "__main__":
    cli()
