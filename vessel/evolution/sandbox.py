import os
import shutil
import subprocess
from loguru import logger

class VesselSandbox:
    """
    A safe, isolated execution environment for Agents to test proposed code changes.
    Acts as a mini CI/CD pipeline to prevent Agents from deploying broken code.
    """
    
    def __init__(self):
        self.backups = {}

    def backup(self, filepath: str) -> str:
        """Creates a backup of the target file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Cannot backup. File not found: {filepath}")
            
        backup_path = f"{filepath}.bak"
        shutil.copy2(filepath, backup_path)
        self.backups[filepath] = backup_path
        logger.info(f"Created backup of {filepath} at {backup_path}")
        return backup_path

    def apply_patch(self, filepath: str, old_code: str, new_code: str) -> None:
        """Applies a string replacement patch to the file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Cannot patch. File not found: {filepath}")
            
        with open(filepath, "r") as f:
            content = f.read()
            
        if old_code not in content:
            raise ValueError(f"Could not find the target code block to replace in {filepath}.")
            
        new_content = content.replace(old_code, new_code)
        
        with open(filepath, "w") as f:
            f.write(new_content)
            
        logger.success(f"Successfully applied patch to {filepath}")

    def rollback(self, filepath: str) -> None:
        """Restores a file from its backup."""
        if filepath not in self.backups:
            raise ValueError(f"No backup exists for {filepath}")
            
        backup_path = self.backups[filepath]
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file missing: {backup_path}")
            
        shutil.copy2(backup_path, filepath)
        os.remove(backup_path)
        del self.backups[filepath]
        logger.warning(f"Rolled back {filepath} to previous state.")

    def run_tests(self, test_filepath: str) -> bool:
        """
        Executes pytest against the specified test file.
        Returns True if tests pass, False if they fail.
        """
        logger.info(f"Running automated tests for {test_filepath}...")
        
        try:
            # We use 'uv run pytest' to ensure it runs in the correct environment context
            result = subprocess.run(
                ["uv", "run", "pytest", test_filepath, "-q"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.success("Tests PASSED in Sandbox.")
                return True
            else:
                logger.error(f"Tests FAILED in Sandbox:\n{result.stdout}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute tests: {e}")
            return False
