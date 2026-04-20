import abc
import time
from typing import Any, Generic, TypeVar, Type, get_args

from loguru import logger
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from vessel.core.exceptions import CircuitBreakerTripped

InputType = TypeVar("InputType", bound=BaseModel)
OutputType = TypeVar("OutputType", bound=BaseModel)

class BaseVessel(Generic[InputType, OutputType], abc.ABC):
    """
    The foundational class for a Fat Skill.
    Enforces strict Pydantic inputs/outputs and provides automatic, stateful retries.
    """

    def __init__(self):
        self._circuit_failure_count = 0
        self._circuit_open_until = 0.0
        self._circuit_failure_threshold = 3
        self._circuit_recovery_time = 3600  # 1 hour

    @abc.abstractmethod
    def execute(self, inputs: InputType) -> OutputType:
        """
        The core deterministic logic of the skill. Must be implemented by the subclass.
        """
        pass

    def _get_input_model(self) -> Type[InputType]:
        """
        Extract the Pydantic model for the input from the class's generic arguments.
        """
        for base in getattr(self.__class__, "__orig_bases__", []):
            if hasattr(base, "__origin__") and issubclass(base.__origin__, BaseVessel):
                args = get_args(base)
                if args:
                    return args[0]
        raise RuntimeError(f"Could not determine InputType for Vessel: {self.__class__.__name__}")

    # Default retry strategy: Stop after 3 attempts, wait exponentially (1s, 2s, 4s).
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _execute_with_retries(self, inputs: InputType) -> OutputType:
        try:
            return self.execute(inputs)
        except Exception as e:
            logger.warning(
                f"Vessel {self.__class__.__name__} execution failed with {type(e).__name__}: {e}. Retrying..."
            )
            raise

    def run(self, raw_input: Any) -> OutputType:
        """
        The entrypoint for the Thin Harness.
        Handles validation, execution tracing, retries, and circuit breaking natively.
        """
        # Circuit Breaker Check
        if time.time() < self._circuit_open_until:
            logger.error(f"Circuit Breaker open for {self.__class__.__name__}. Rejecting execution.")
            raise CircuitBreakerTripped(self.__class__.__name__)

        input_model = self._get_input_model()

        # Phase 1: Strict Validation
        try:
            inputs = input_model.model_validate(raw_input)
        except ValidationError as e:
            logger.error(f"Schema Validation failed for {self.__class__.__name__}: {e}")
            raise

        # Phase 2: Deterministic Execution with Self-Healing
        logger.info(f"Starting execution of {self.__class__.__name__}...")
        try:
            result = self._execute_with_retries(inputs)
            self._circuit_failure_count = 0  # Reset on success
            logger.info(f"Successfully executed {self.__class__.__name__}.")
            return result
        except Exception as e:
            self._circuit_failure_count += 1
            if self._circuit_failure_count >= self._circuit_failure_threshold:
                logger.error(
                    f"Circuit Breaker tripped for {self.__class__.__name__} after "
                    f"{self._circuit_failure_count} consecutive run failures."
                )
                self._circuit_open_until = time.time() + self._circuit_recovery_time
            raise

