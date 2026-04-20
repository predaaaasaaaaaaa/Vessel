import pytest
from pydantic import BaseModel
from vessel.core.base import BaseVessel
from vessel.core.exceptions import CircuitBreakerTripped

class CBInput(BaseModel):
    val: int

class CBOutput(BaseModel):
    result: str

class FailingVessel(BaseVessel[CBInput, CBOutput]):
    """A Vessel that always fails, to test circuit breaking."""
    def __init__(self):
        super().__init__()
        self.call_count = 0

    def execute(self, inputs: CBInput) -> CBOutput:
        self.call_count += 1
        raise ValueError("Simulated catastrophic API failure")

def test_vessel_circuit_breaker_trips():
    """Test that repeated failures across runs trip the circuit breaker."""
    vessel = FailingVessel()
    
    # We expect the internal retries to happen on each run.
    # But after 3 full run failures (default threshold), the circuit should open.
    
    for _ in range(3):
        with pytest.raises(Exception) as excinfo:
            vessel.run({"val": 1})
        # Ensure it's not the CircuitBreakerTripped exception yet
        assert not isinstance(excinfo.value, CircuitBreakerTripped)
        
    # The 4th run should instantly raise a CircuitBreakerTripped exception
    # without even trying to execute or retry.
    initial_call_count = vessel.call_count
    with pytest.raises(CircuitBreakerTripped):
        vessel.run({"val": 1})
        
    # Verify the execute method wasn't called again because the circuit was open
    assert vessel.call_count == initial_call_count
