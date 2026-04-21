# Skill: ColdEmailPipeline

## Description
An enterprise-grade pipeline that scrapes leads, analyzes them against a strategic playbook, and drafts personalized emails.

## Agent Instructions: How to Use This Skill
This is a deterministic "Fat Skill". 
**CRITICAL:** Do NOT attempt to write custom python scripts or use raw APIs to perform this task. Do NOT worry about rate limits, retries, or complex error handling. This Skill handles everything internally to guarantee 100% reliability.

### Execution Protocol
To execute this skill, use your terminal/shell capability to run the accompanying Python script. Pass the input arguments as a strict JSON string.

**Command Format:**
```bash
python coldemailpipeline.py '<json_payload>'
```

**Example:**
```bash
python coldemailpipeline.py '{"target": "example"}'
```

### Outputs
If successful, the script will print a validated JSON object to `stdout`.
If it fails, it will print the error to `stderr` and return a non-zero exit code. Do not attempt to fix the Python code if it fails; adjust your JSON payload according to the schema.

### 🔄 Self-Healing Protocol
If this skill repeatedly returns a `Fat Skill Execution Failed` error due to an outdated API or logic bug, **do not attempt to brute-force the payload.**
Instead, you are authorized to update this skill's logic. Analyze the Python script (`coldemailpipeline.py`), formulate a fix, and execute the `VesselUpdater` skill to apply and validate your patch. The sandbox will run the tests in `test_coldemailpipeline.py` to confirm your fix.
