from typing import Any, Dict
from loguru import logger
from pydantic import BaseModel

from vessel.core.base import BaseVessel

class VesselHarness:
    """
    The Thin Harness Orchestrator.
    Allows developers to programmatically register and route payloads to a fleet of Fat Skills.
    """
    def __init__(self):
        self.vessels: Dict[str, BaseVessel] = {}

    def register(self, vessel: BaseVessel) -> None:
        """
        Registers a Fat Skill instance into the Harness.
        """
        name = vessel.__class__.__name__
        self.vessels[name] = vessel
        logger.info(f"Registered Vessel: {name} in the Harness.")

    def route(self, vessel_name: str, payload: Any) -> BaseModel:
        """
        Routes a raw JSON/Dict payload to the specified Vessel.
        Returns the strictly validated Pydantic output.
        """
        if vessel_name not in self.vessels:
            logger.error(f"Attempted to route to unknown Vessel: {vessel_name}")
            raise ValueError(f"Unknown Vessel: {vessel_name}")
            
        vessel = self.vessels[vessel_name]
        logger.info(f"Routing payload to {vessel_name}...")
        
        # The Vessel handles its own validation, retries, and circuit breaking
        return vessel.run(payload)
