from pydantic import BaseModel, Field
from loguru import logger

from vessel.core.base import BaseVessel
from vessel.evolution.sandbox import VesselSandbox

class UpdaterInput(BaseModel):
    target_filepath: str = Field(..., description="The absolute or relative path to the Vessel .py file to update.")
    test_filepath: str = Field(..., description="The absolute or relative path to the pytest file that validates the target.")
    old_code: str = Field(..., description="The exact literal string of code to be replaced. Must be an exact match.")
    new_code: str = Field(..., description="The new string of code to insert in place of the old_code.")
    reason: str = Field(..., description="A brief explanation of why this patch is necessary (e.g., 'API structure changed').")

class UpdaterOutput(BaseModel):
    status: str
    details: str

class VesselUpdater(BaseVessel[UpdaterInput, UpdaterOutput]):
    """
    A Meta-Skill that allows an Agent to safely patch and test other Vessels.
    Forces the Agent to run changes through a strict Sandbox CI/CD loop.
    """
    
    def __init__(self):
        super().__init__()
        self.sandbox = VesselSandbox()

    def execute(self, inputs: UpdaterInput) -> UpdaterOutput:
        logger.info(f"VesselUpdater initiated for {inputs.target_filepath}")
        logger.info(f"Reason for evolution: {inputs.reason}")
        
        # 1. Backup
        try:
            self.sandbox.backup(inputs.target_filepath)
        except Exception as e:
            return UpdaterOutput(status="Failed", details=f"Could not backup file: {e}")
            
        # 2. Patch
        try:
            self.sandbox.apply_patch(inputs.target_filepath, inputs.old_code, inputs.new_code)
        except Exception as e:
            self.sandbox.rollback(inputs.target_filepath)
            return UpdaterOutput(status="Failed", details=f"Failed to apply patch. Rolled back. Error: {e}")
            
        # 3. Test (The Crucible)
        tests_passed = self.sandbox.run_tests(inputs.test_filepath)
        
        # 4. Deploy or Rollback
        if tests_passed:
            logger.success(f"Vessel {inputs.target_filepath} has been successfully evolved and tested.")
            return UpdaterOutput(
                status="Success", 
                details="Successfully evolved. The patch passed all automated tests and is now in production."
            )
        else:
            logger.warning(f"Proposed patch for {inputs.target_filepath} failed tests. Rolling back.")
            self.sandbox.rollback(inputs.target_filepath)
            return UpdaterOutput(
                status="Failed", 
                details="The proposed patch failed the automated test suite. Rolled back to original code. Please analyze the test failure and try a different patch."
            )
