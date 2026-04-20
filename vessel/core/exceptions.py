class VesselError(Exception):
    """Base exception for all Vessel-related errors."""
    pass

class CircuitBreakerTripped(VesselError):
    """
    Raised when a Vessel's circuit breaker is open.
    This prevents the Agent from continually hammering a down API.
    """
    def __init__(self, vessel_name: str, message: str = None):
        self.vessel_name = vessel_name
        super().__init__(message or f"Circuit Breaker tripped for {vessel_name}. The skill is temporarily disabled.")
