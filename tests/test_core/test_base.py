import pytest
from pydantic import BaseModel, ValidationError
from vessel.core.base import BaseVessel

class TestInput(BaseModel):
    target_name: str

class TestOutput(BaseModel):
    status: str
    attempts_taken: int

class FlakyVessel(BaseVessel[TestInput, TestOutput]):
    """
    A mock Vessel that simulates a transient failure.
    It will fail twice before succeeding on the third attempt.
    """
    def __init__(self):
        super().__init__()
        self.attempts = 0

    def execute(self, inputs: TestInput) -> TestOutput:
        self.attempts += 1
        if self.attempts < 3:
            raise ValueError("Simulated transient network error")
        return TestOutput(status=f"Success for {inputs.target_name}", attempts_taken=self.attempts)

def test_vessel_successful_execution_with_retries():
    """Test that the Vessel automatically retries and succeeds."""
    vessel = FlakyVessel()
    
    # We call .run() which is the Harness-facing wrapper that provides retries/validation
    inputs = TestInput(target_name="Alpha")
    result = vessel.run(inputs)
    
    assert result.status == "Success for Alpha"
    assert result.attempts_taken == 3
    assert vessel.attempts == 3

def test_vessel_dict_input_parsing():
    """Test that the Vessel can accept a raw dictionary and parse it into the Input schema."""
    vessel = FlakyVessel()
    
    # The Harness should be able to pass a dictionary (e.g., raw JSON from an LLM)
    raw_llm_input = {"target_name": "Bravo"}
    result = vessel.run(raw_llm_input)
    
    assert result.status == "Success for Bravo"

def test_vessel_strict_validation_failure():
    """Test that the Vessel raises a clear validation error on bad input."""
    vessel = FlakyVessel()
    
    # Passing invalid schema data
    bad_input = {"wrong_key": "Charlie"}
    
    with pytest.raises(ValidationError):
        vessel.run(bad_input)
