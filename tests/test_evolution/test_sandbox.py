import os
from vessel.evolution.sandbox import VesselSandbox

def test_sandbox_apply_and_rollback(tmp_path):
    """Test that a Sandbox can backup a file, apply a patch, and rollback if needed."""
    
    # 1. Setup a dummy file in the temp path
    dummy_file = tmp_path / "dummy_vessel.py"
    initial_code = "print('Hello World')\n"
    dummy_file.write_text(initial_code)
    
    sandbox = VesselSandbox()
    
    # 2. Backup the file
    backup_path = sandbox.backup(str(dummy_file))
    assert os.path.exists(backup_path)
    
    # 3. Apply a patch
    new_code = "print('Hello Evolved World')\n"
    sandbox.apply_patch(str(dummy_file), initial_code.strip(), new_code.strip())
    
    assert dummy_file.read_text() == new_code
    
    # 4. Rollback
    sandbox.rollback(str(dummy_file))
    assert dummy_file.read_text() == initial_code

def test_sandbox_test_execution(tmp_path):
    """Test that a Sandbox can run a pytest suite against a file."""
    
    # 1. Setup a dummy test file
    test_file = tmp_path / "test_dummy.py"
    test_file.write_text('''
def test_success():
    assert True
''')
    
    sandbox = VesselSandbox()
    
    # 2. Run the tests. It should return True.
    assert sandbox.run_tests(str(test_file)) is True
    
    # 3. Break the test file
    test_file.write_text('''
def test_failure():
    assert False
''')
    
    # 4. Run the tests again. It should return False.
    assert sandbox.run_tests(str(test_file)) is False
