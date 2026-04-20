from typing import Generic, TypeVar
from pydantic import BaseModel
from vessel.core.base import BaseVessel

InputType = TypeVar("InputType", bound=BaseModel)
OutputType = TypeVar("OutputType", bound=BaseModel)

class VesselPipeline(BaseVessel[InputType, OutputType], Generic[InputType, OutputType]):
    """
    A specialized Vessel designed to chain multiple Fat Skills together.
    Since it inherits from BaseVessel, the entire pipeline benefits from
    strict Pydantic I/O validation and top-level Circuit Breaking.
    """
    pass
