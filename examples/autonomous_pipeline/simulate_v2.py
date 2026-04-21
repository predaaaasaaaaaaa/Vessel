import os
import sys
import json
from loguru import logger

# Import the Meta-Skill from the Vessel core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from vessel.evolution.updater import VesselUpdater

def simulate_agent_self_healing():
    """
    Simulates an Agent (like OpenClaw) discovering a bug and using VesselUpdater to fix it.
    """
    logger.info("--- STARTING SELF-HEALING SIMULATION ---")
    
    # 1. Setup a broken skill
    with open("broken_skill.py", "w") as f:
        f.write('''
def run_logic():
    return "The result is 1"
''')

    # 2. Setup the deterministic test that the fix MUST pass
    with open("test_broken_skill.py", "w") as f:
        f.write('''
from broken_skill import run_logic
def test_fix():
    assert run_logic() == "The result is 2"  # This currently fails!
''')

    updater = VesselUpdater()
    
    # 3. Simulate the Agent calling the VesselUpdater skill with a patch
    agent_payload = {
        "target_filepath": "broken_skill.py",
        "test_filepath": "test_broken_skill.py",
        "old_code": 'return "The result is 1"',
        "new_code": 'return "The result is 2"',
        "reason": "Agent realized the requirement changed from 1 to 2."
    }
    
    logger.info("Agent is calling VesselUpdater to evolve 'broken_skill.py'...")
    result = updater.run(agent_payload)
    
    logger.info(f"VesselUpdater Result: {result.status}")
    logger.info(f"VesselUpdater Details: {result.details}")
    
    # 4. Verify the file was actually updated
    with open("broken_skill.py", "r") as f:
        final_code = f.read()
        logger.info(f"Final Code in broken_skill.py:\\n{final_code.strip()}")

if __name__ == "__main__":
    simulate_agent_self_healing()
