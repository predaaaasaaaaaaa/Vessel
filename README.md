<div align="center">
  
# 🚢 Vessel
**The Next.js of Agentic Skills.**

<img src="docs/cli-screenshot.svg" alt="Vessel CLI Demo" width="800">

*Stop trying to teach your AI Agent how to handle rate limits, network failures, and bad JSON. Give it a **Fat Skill** instead.*

</div>

---

## The Problem: "Skillification Exhaustion"

If you've built AI Agents, you know the pain:
1. You ask your Agent (OpenClaw, Claude, Hermes) to do something complex: *"Find SaaS leads and verify their emails."*
2. The Agent writes a Python script on the fly. It hits a rate limit (429). It crashes.
3. You prompt the Agent: *"If you hit a 429, wait 60 seconds."*
4. It tries again. It gets an unexpected JSON response. It crashes.
5. You prompt the Agent: *"Expect this exact JSON schema and ignore missing fields."*
6. Three days later, it finally works. You tell the Agent: **"SKILLIFY THIS."**
7. Next week, the API changes slightly. The prompt-based skill breaks. The cycle begins again.

LLMs are brilliant reasoning engines, but they are **terrible execution environments**.

## The Solution (V1): "Thin Harness + Fat Skill"

**Vessel** is a framework that fundamentally changes how Agents interact with the real world. 

Instead of forcing the LLM to learn how to handle network blips, pagination, and data parsing through sheer trial and error, **Vessel pre-packages all of that resilience into deterministic, self-healing Python code.**

When an Agent uses a Vessel, it doesn't write code. It doesn't worry about failures. It just passes a strict JSON payload to the Vessel, and the Vessel guarantees a perfect, validated result back.

---

## 🏗️ Project Architecture

Vessel is designed around a strict separation of concerns, providing both a robust Python framework and a zero-friction Developer Experience (DX).

```text
vessel/
├── core/                # The execution engine
│   ├── base.py          # BaseVessel: Retries, circuit-breaking, validation
│   ├── exceptions.py    # Custom errors (e.g., CircuitBreakerTripped)
│   └── pipeline.py      # VesselPipeline: Orchestrates multiple sub-vessels
├── mcp/                 # The Agentic Bridge
│   ├── adapter.py       # Auto-translates Pydantic schemas to MCP Tool JSON
│   └── server.py        # Exposes local Vessels to any MCP-compatible agent
├── evolution/           # The Self-Healing Sandbox
│   ├── sandbox.py       # Isolated CI/CD pipeline (Backup, Patch, Test, Rollback)
│   └── updater.py       # VesselUpdater: The Meta-Skill Agents use to fix bugs
└── cli/                 # The Next.js-style DX
    ├── main.py          # The interactive wizard and test runner (`vessel create`, `vessel test`)
    ├── llm.py           # The "Lead Agentic Architect" system prompt for autonomous generation
    └── config.py        # Secure API key management (`vessel config`)
```

---

## ⚡️ For Beginners: Zero-Friction Creation

You don't need to be a Python expert to build 100% reliable tools.

1. **Run the Wizard:**
```bash
vessel create
```
The stunning, interactive CLI will ask you what you want to build.

2. **The Magic Output:**
Vessel instantly generates:
*   `leadgenvessel.py`: A robust, self-healing Python script (the "Fat Skill").
*   `test_leadgenvessel.py`: An automated test suite for your skill.
*   `LeadGenVessel_SKILL.md`: The exact instruction manual your Agent needs.

3. **Deploy to your Agent:**
Drag and drop those files into your OpenClaw or Hermes workspace. The `.md` file tells the Agent exactly how to use the `.py` script via the terminal. **100% portable. Zero servers required.**

---

## 🛠 For Pro Devs: Absolute Control

Vessel exposes a powerful, heavily typed architecture for building enterprise-grade tools.

### 1. Strict I/O Validation (Pydantic)
If an API returns garbage, Pydantic catches it *inside the Vessel*. It raises a clear error instead of passing hallucinated data back to your LLM context.

### 2. Stateful Retries (Tenacity)
Network blips happen. Vessels automatically wrap your `execute()` method in exponential backoff retries. The Agent never even knows a failure occurred.

### 3. Circuit Breaking
If an API is hard-down (e.g., 3 consecutive run failures), Vessel trips a **Circuit Breaker**. It instantly rejects further requests for the next hour, saving your Agent from infinite retry loops and drained API credits.

### Example: Building a Vessel

```python
from pydantic import BaseModel
from vessel.core.base import BaseVessel

class WeatherInput(BaseModel):
    location: str

class WeatherOutput(BaseModel):
    temperature: float
    status: str

# BaseVessel handles Retries, Validation, and Circuit Breaking automatically!
class WeatherVessel(BaseVessel[WeatherInput, WeatherOutput]):
    """Fetches the current weather for a given location."""
    
    def execute(self, inputs: WeatherInput) -> WeatherOutput:
        # Your deterministic logic here. 
        # If this throws an exception, Vessel will automatically back off and retry.
        return WeatherOutput(temperature=72.5, status="Sunny")
```

---

## 🚀 V2: Autonomous Self-Healing & Pipelines

Vessel V2 elevates the framework from a set of reliable tools to an **Autonomous Self-Healing System**. 

### 1. LLM Architect (`vessel config`)
Vessel can now write the code for you. 
Run `vessel config` to securely store your OpenAI API key locally. When you run `vessel create`, Vessel's internal "Lead Agentic Architect" prompt will generate the full, production-ready python code, tests, and documentation automatically.

### 2. Multi-Agent Pipelines (`VesselPipeline`)
Don't build monoliths. V2 introduces `VesselPipeline`, allowing you to compose dozens of isolated sub-vessels (e.g., `ScraperVessel` -> `AnalyzerVessel` -> `DrafterVessel`) into a single, unified skill for your Agent. If step 3 fails, only step 3 retries.

### 3. Safe Self-Evolution (`VesselUpdater` & `VesselSandbox`)
What happens when an API changes and the python script breaks?
With V2, your Agent doesn't need you to fix it. The auto-generated `SKILL.md` instructs the Agent to use the built-in **`VesselUpdater`** Meta-Skill.
1. The Agent proposes a code fix.
2. The `VesselSandbox` intercepts it, creates a backup, and patches the file in an isolated environment.
3. It automatically runs the `pytest` suite. 
4. If the tests pass, the fix is deployed. If they fail, it rolls back instantly. **Your Agent can write its own code, but it can never break production.**

---

## 🔌 The MCP Server (Optional)

Do you use Claude Desktop or an Agent that supports the **Model Context Protocol (MCP)**? 

Vessel has a built-in dynamic adapter. Point the Vessel server at your skills directory, and it will instantly translate your Pydantic schemas into native MCP Tools over `stdio`.

```bash
vessel serve ./my_skills_directory
```

---

## 📦 Installation & Upgrading

```bash
# Requires Python >= 3.11
pip install vessel
```
*(Or use `uv` for lightning-fast installation!)*

**Zero-Friction Updates:**
When a new version of Vessel drops on GitHub, simply run:
```bash
vessel update
```

---

<div align="center">
  <i>Built for the next generation of autonomous systems.</i>
</div>
