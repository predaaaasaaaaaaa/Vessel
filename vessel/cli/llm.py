import json
import urllib.request
import urllib.error
from typing import Dict

SYSTEM_PROMPT = """You are the Lead Agentic Architect for the 'Vessel' framework.
Vessel is a framework for building Deterministic, Self-Healing, and Hot-Swappable "Fat Skills" for AI agents.

RULES FOR ARCHITECTING FAT SKILLS:
1. The Composition Rule (No Monoliths): Break complex user requests down into atomic, single-purpose steps (e.g., ScraperVessel, VerifierVessel). NEVER generate a single massive BaseVessel.
2. The Pipeline Rule: Generate a `VesselPipeline` class that orchestrates these sub-vessels using the `self.harness.route()` pattern internally, or by instantiating them directly and calling `.run()`. If a step fails catastrophically, the pipeline halts safely.
3. The Strict Schema Rule: Every sub-vessel MUST have strictly defined Pydantic Input and Output schemas.
4. You must implement robust deterministic logic in the `execute` methods. Use logging (`from loguru import logger`).

OUTPUT FORMAT:
You must return a STRICT JSON object with exactly three keys:
- "python_code": The complete content of the Python file (including imports, models, Sub-Vessels, the master Pipeline, and the `if __name__ == "__main__":` executable block).
- "test_code": The complete content of the pytest file for this Vessel.
- "markdown_docs": The complete content of the SKILL.md file with the `🔄 Self-Healing Protocol`.

Do not include any Markdown wrapping (like ```json) around the JSON payload itself. Ensure the JSON is valid and parsable.
"""

def generate_vessel_code(api_key: str, name: str, description: str) -> Dict[str, str]:
    """Calls the OpenAI API to dynamically architect the Vessel code."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = f"Name: {name}\nDescription: {description}\nGenerate the complete Fat Skill pipeline, test suite, and SKILL.md according to the rules."
    
    data = {
        "model": "gpt-4o",  # Prefer a highly capable model for architecture
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode("utf-8")
            response_json = json.loads(response_body)
            content = response_json["choices"][0]["message"]["content"]
            return json.loads(content)
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        raise Exception(f"OpenAI API HTTP Error {e.code}: {error_msg}")
    except Exception as e:
        raise Exception(f"Failed to communicate with OpenAI: {str(e)}")
