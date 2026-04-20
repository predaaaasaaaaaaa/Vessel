import os
from pydantic import BaseModel
from vessel.evolution.updater import VesselUpdater, UpdaterInput

def test_vessel_updater_success(tmp_path):
    """Test that the Meta-Skill can successfully patch and test a Vessel."""
    
    # 1. Setup a dummy target vessel and its test
    target_vessel = tmp_path / "target_vessel.py"
    target_vessel.write_text("def my_func(): return 1")
    
    target_test = tmp_path / "test_target_vessel.py"
    target_test.write_text('''
from target_vessel import my_func
def test_my_func():
    assert my_func() == 2  # Will pass after the patch
''')
    
    updater = VesselUpdater()
    
    # 2. Execute the Updater skill
    payload = UpdaterInput(
        target_filepath=str(target_vessel),
        test_filepath=str(target_test),
        old_code="return 1",
        new_code="return 2",
        reason="Update function to return 2"
    )
    
    result = updater.run({"target_filepath": str(target_vessel), "test_filepath": str(target_test), "old_code": "return 1", "new_code": "return 2", "reason": "Update function to return 2"})
    
    # 3. Assert success
    assert result.status == "Success"
    assert "Successfully evolved" in result.details
    assert target_vessel.read_text() == "def my_func(): return 2"

def test_vessel_updater_rollback_on_failure(tmp_path):
    """Test that the Meta-Skill rolls back changes if tests fail."""
    
    # 1. Setup a dummy target vessel and a test that WILL FAIL
    target_vessel = tmp_path / "target_vessel_broken.py"
    target_vessel.write_text("def my_func(): return 1")
    
    target_test = tmp_path / "test_target_vessel_broken.py"
    target_test.write_text('''
from target_vessel_broken import my_func
def test_my_func():
    assert my_func() == 1  # Will fail after the patch changes it to 3
''')
    
    updater = VesselUpdater()
    
    # 2. Execute the Updater skill with a bad patch
    payload = {
        "target_filepath": str(target_vessel),
        "test_filepath": str(target_test),
        "old_code": "return 1",
        "new_code": "return 3",
        "reason": "Agent hallucinated a bad fix"
    }
    
    result = updater.run(payload)
    
    # 3. Assert failure and rollback
    assert result.status == "Failed"
    assert "Rolled back" in result.details
    assert target_vessel.read_text() == "def my_func(): return 1"  # File should be unchanged
