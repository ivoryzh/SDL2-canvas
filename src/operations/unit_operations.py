"""
Unit Operation handlers for SDL2 Canvas Integration.
"""
import logging
import json
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from src.api.sdl2_client import SDL2Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("unit_operations")


class UnitOperation(ABC):
    """Base class for all unit operations."""

    def __init__(self, params: Dict[str, Any], client: SDL2Client):
        """
        Initialize the unit operation.

        Args:
            params: Parameters for the unit operation
            client: SDL2 API client
        """
        self.params = params
        self.client = client
        self.result = None

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the unit operation.

        Returns:
            Result of the operation
        """
        pass

    def save_result(self, result_file: str) -> None:
        """
        Save the result to a file.

        Args:
            result_file: Path to the result file
        """
        if self.result:
            with open(result_file, 'w') as f:
                json.dump(self.result, f, indent=2)
            logger.info(f"Saved result to {result_file}")


class CVOperation(UnitOperation):
    """Cyclic Voltammetry operation."""

    def execute(self) -> Dict[str, Any]:
        """
        Execute a CV task.

        Returns:
            Result of the CV operation
        """
        # Extract parameters
        v_range = self.params.get("v_range", [-0.5, 0.5])
        freq = self.params.get("freq", 0.1)

        # Create payload
        payload = {
            "v_range": v_range,
            "freq": freq
        }

        # Create task
        task_data = self.client.create_task("cv", payload)

        # Wait for completion
        completed_task = self.client.wait_for_task_completion(task_data["id"])

        # Store result
        self.result = completed_task

        return completed_task


class RollingMeanOperation(UnitOperation):
    """Rolling Mean operation."""

    def execute(self) -> Dict[str, Any]:
        """
        Execute a rolling mean task.

        Returns:
            Result of the rolling mean operation
        """
        # Extract parameters
        csv_id = self.params.get("csv_id")
        x_col = self.params.get("x_col", "time")
        y_col = self.params.get("y_col", "current")
        window_size = self.params.get("window_size", 20)
        min_periods = self.params.get("min_periods")

        # Create payload
        payload = {
            "csv_id": csv_id,
            "x_col": x_col,
            "y_col": y_col,
            "window_size": window_size
        }

        if min_periods is not None:
            payload["min_periods"] = min_periods

        # Create task
        task_data = self.client.create_task("rolling_mean", payload)

        # Wait for completion
        completed_task = self.client.wait_for_task_completion(task_data["id"])

        # Store result
        self.result = completed_task

        return completed_task


class PeakDetectionOperation(UnitOperation):
    """Peak Detection operation."""

    def execute(self) -> Dict[str, Any]:
        """
        Execute a peak detection task.

        Returns:
            Result of the peak detection operation
        """
        # Extract parameters
        csv_id = self.params.get("csv_id")
        x_col = self.params.get("x_col", "voltage")
        y_col = self.params.get("y_col", "current")
        height = self.params.get("height")
        prominence = self.params.get("prominence", 0.02)
        distance = self.params.get("distance")
        width = self.params.get("width")
        threshold = self.params.get("threshold")

        # Create payload
        payload = {
            "csv_id": csv_id,
            "x_col": x_col,
            "y_col": y_col,
            "prominence": prominence
        }

        # Add optional parameters if provided
        if height is not None:
            payload["height"] = height
        if distance is not None:
            payload["distance"] = distance
        if width is not None:
            payload["width"] = width
        if threshold is not None:
            payload["threshold"] = threshold

        # Create task
        task_data = self.client.create_task("peak_detection", payload)

        # Wait for completion
        completed_task = self.client.wait_for_task_completion(task_data["id"])

        # Store result
        self.result = completed_task

        return completed_task


# Factory function to create the appropriate unit operation
def create_unit_operation(operation_type: str, params: Dict[str, Any], client: SDL2Client) -> UnitOperation:
    """
    Create a unit operation based on the operation type.

    Args:
        operation_type: Type of unit operation
        params: Parameters for the unit operation
        client: SDL2 API client

    Returns:
        Unit operation instance

    Raises:
        ValueError: If the operation type is not supported
    """
    if operation_type == "uo_sdl2_cv":
        return CVOperation(params, client)
    elif operation_type == "uo_sdl2_rolling_mean":
        return RollingMeanOperation(params, client)
    elif operation_type == "uo_sdl2_peak_detection":
        return PeakDetectionOperation(params, client)
    else:
        raise ValueError(f"Unsupported operation type: {operation_type}")
