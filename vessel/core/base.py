import abc
import time
import json
import tempfile
from pathlib import Path
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
        self._circuit_failure_threshold = 3
        self._circuit_recovery_time = 3600  # 1 hour
        # Persist circuit breaker state across independent CLI executions
        self._cb_state_file = Path(tempfile.gettempdir()) / f"vessel_cb_{self.__class__.__name__}.json"

    def _get_cb_state(self) -> dict:
        if self._cb_state_file.exists():
            try:
                return json.loads(self._cb_state_file.read_text())
            except Exception:
                pass
        return {"failure_count": 0, "open_until": 0.0}

    def _save_cb_state(self, state: dict):
        try:
            self._cb_state_file.write_text(json.dumps(state))
        except Exception as e:
            logger.warning(f"Could not save circuit breaker state: {e}")

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
        cb_state = self._get_cb_state()
        if time.time() < cb_state["open_until"]:
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
            if cb_state["failure_count"] > 0:
                cb_state["failure_count"] = 0
                self._save_cb_state(cb_state)
            logger.info(f"Successfully executed {self.__class__.__name__}.")
            return result
        except Exception as e:
            cb_state["failure_count"] += 1
            if cb_state["failure_count"] >= self._circuit_failure_threshold:
                logger.error(
                    f"Circuit Breaker tripped for {self.__class__.__name__} after "
                    f"{cb_state['failure_count']} consecutive run failures."
                )
                cb_state["open_until"] = time.time() + self._circuit_recovery_time
            self._save_cb_state(cb_state)
            raise

