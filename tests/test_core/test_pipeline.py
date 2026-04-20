import pytest
from pydantic import BaseModel
from vessel.core.pipeline import VesselPipeline
from vessel.core.base import BaseVessel

# Define Dummy Sub-Vessels for the Pipeline

class StepOneInput(BaseModel):
    text: str

class StepOneOutput(BaseModel):
    extracted_data: str

class StepOneVessel(BaseVessel[StepOneInput, StepOneOutput]):
    def execute(self, inputs: StepOneInput) -> StepOneOutput:
        return StepOneOutput(extracted_data=f"Extracted: {inputs.text}")

class StepTwoInput(BaseModel):
    data: str

class StepTwoOutput(BaseModel):
    final_result: str

class StepTwoVessel(BaseVessel[StepTwoInput, StepTwoOutput]):
    def execute(self, inputs: StepTwoInput) -> StepTwoOutput:
        return StepTwoOutput(final_result=f"Processed: {inputs.data}")


# Define the Pipeline

class MyPipelineInput(BaseModel):
    raw_text: str

class MyPipelineOutput(BaseModel):
    output: str

class MyPipeline(VesselPipeline[MyPipelineInput, MyPipelineOutput]):
    def __init__(self):
        super().__init__()
        self.step_one = StepOneVessel()
        self.step_two = StepTwoVessel()

    def execute(self, inputs: MyPipelineInput) -> MyPipelineOutput:
        # Route through Step 1
        res1 = self.step_one.run({"text": inputs.raw_text})
        
        # Route through Step 2
        res2 = self.step_two.run({"data": res1.extracted_data})
        
        return MyPipelineOutput(output=res2.final_result)


def test_pipeline_execution():
    """Test that a Pipeline correctly chains multiple Vessels together."""
    pipeline = MyPipeline()
    result = pipeline.run({"raw_text": "Hello World"})
    
    assert result.output == "Processed: Extracted: Hello World"
