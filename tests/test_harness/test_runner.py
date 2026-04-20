import pytest
from pydantic import BaseModel
from vessel.core.base import BaseVessel
from vessel.harness.runner import VesselHarness

class MockInput(BaseModel):
    val: str

class MockOutput(BaseModel):
    result: str

class AlphaVessel(BaseVessel[MockInput, MockOutput]):
    def execute(self, inputs: MockInput) -> MockOutput:
        return MockOutput(result=f"Alpha: {inputs.val}")

class BravoVessel(BaseVessel[MockInput, MockOutput]):
    def execute(self, inputs: MockInput) -> MockOutput:
        return MockOutput(result=f"Bravo: {inputs.val}")

def test_harness_registration_and_routing():
    """Test that a Harness can register multiple Vessels and route payloads correctly."""
    harness = VesselHarness()
    
    # 1. Registration
    harness.register(AlphaVessel())
    harness.register(BravoVessel())
    
    # Ensure they are registered by class name
    assert "AlphaVessel" in harness.vessels
    assert "BravoVessel" in harness.vessels
    
    # 2. Routing
    # Send a raw dictionary (like what an LLM would produce) to the specific Vessel
    alpha_result = harness.route("AlphaVessel", {"val": "test1"})
    bravo_result = harness.route("BravoVessel", {"val": "test2"})
    
    # Verify outputs
    assert alpha_result.result == "Alpha: test1"
    assert bravo_result.result == "Bravo: test2"

def test_harness_unknown_vessel():
    """Test that the harness rejects routing to unregistered Vessels."""
    harness = VesselHarness()
    
    with pytest.raises(ValueError, match="Unknown Vessel: CharlieVessel"):
        harness.route("CharlieVessel", {"val": "test"})
