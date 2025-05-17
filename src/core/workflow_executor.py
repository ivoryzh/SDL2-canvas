"""
Workflow Executor for SDL2 Canvas Integration.
"""
import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional, Union
from src.api.sdl2_client import SDL2Client
from src.operations.unit_operations import create_unit_operation
from src.utils.config import CANVAS_RESULT_FILE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("workflow_executor")


class WorkflowExecutor:
    """Executor for Canvas workflows with SDL2."""

    def __init__(self, client: Optional[SDL2Client] = None):
        """
        Initialize the workflow executor.

        Args:
            client: SDL2 API client (optional, will create one if not provided)
        """
        self.client = client or SDL2Client()
        self.workflow = None
        self.results = {}
        self.operation_results = {}

    def load_workflow(self, workflow_file: str) -> Dict[str, Any]:
        """
        Load a workflow from a JSON file.

        Args:
            workflow_file: Path to the workflow JSON file

        Returns:
            Workflow data
        """
        try:
            with open(workflow_file, 'r') as f:
                self.workflow = json.load(f)
            logger.info(f"Loaded workflow from {workflow_file}")
            return self.workflow
        except Exception as e:
            logger.error(f"Error loading workflow: {str(e)}")
            raise

    def execute_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single operation in the workflow.

        Args:
            operation_data: Operation data including type and parameters

        Returns:
            Result of the operation
        """
        operation_id = operation_data.get("id", "unknown")
        operation_type = operation_data.get("type")
        params = operation_data.get("params", {})

        if not operation_type:
            raise ValueError(f"Operation type not specified for operation {operation_id}")

        logger.info(f"Executing operation {operation_id} of type {operation_type}")

        # Create and execute the appropriate unit operation
        operation = create_unit_operation(operation_type, params, self.client)
        result = operation.execute()

        # Store the result
        self.operation_results[operation_id] = result

        return result

    def resolve_dependencies(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve dependencies in operation parameters.

        Args:
            operation_data: Operation data including parameters

        Returns:
            Operation data with resolved parameters
        """
        params = operation_data.get("params", {})
        resolved_params = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # This is a reference to a previous operation result
                ref_parts = value[1:].split(".")
                ref_op_id = ref_parts[0]

                if ref_op_id not in self.operation_results:
                    raise ValueError(f"Referenced operation {ref_op_id} not found or not executed yet")

                ref_result = self.operation_results[ref_op_id]

                # Navigate through the result structure
                for part in ref_parts[1:]:
                    if part in ref_result:
                        ref_result = ref_result[part]
                    else:
                        raise ValueError(f"Referenced path {value} not found in operation {ref_op_id} result")

                resolved_params[key] = ref_result
            else:
                resolved_params[key] = value

        # Create a new operation data dict with resolved parameters
        resolved_operation = operation_data.copy()
        resolved_operation["params"] = resolved_params

        return resolved_operation

    def execute_workflow(self) -> Dict[str, Any]:
        """
        Execute the loaded workflow.

        Returns:
            Results of the workflow execution
        """
        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow first.")

        workflow_name = self.workflow.get("name", "Unnamed")
        operations = self.workflow.get("operations", [])

        logger.info(f"Executing workflow: {workflow_name} with {len(operations)} operations")

        # Reset operation results
        self.operation_results = {}

        # Execute each operation in sequence
        for operation in operations:
            # Resolve dependencies
            resolved_operation = self.resolve_dependencies(operation)

            # Execute the operation
            result = self.execute_operation(resolved_operation)

            # If this is the last operation, use its result as the workflow result
            if operation == operations[-1]:
                self.results = result

        # Save to result file
        self.save_results(CANVAS_RESULT_FILE)

        return self.results

    def save_results(self, result_file: str) -> None:
        """
        Save the results to a file.

        Args:
            result_file: Path to the result file
        """
        if self.results:
            with open(result_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Saved results to {result_file}")

    def execute_pipeline(self, workflow_file: str) -> Dict[str, Any]:
        """
        Load and execute a workflow pipeline.

        Args:
            workflow_file: Path to the workflow JSON file

        Returns:
            Results of the pipeline execution
        """
        self.load_workflow(workflow_file)
        return self.execute_workflow()


def main():
    """Main entry point for the workflow executor."""
    parser = argparse.ArgumentParser(description="SDL2 Canvas Workflow Executor")
    parser.add_argument("workflow_file", help="Path to the workflow JSON file")
    parser.add_argument("--result-file", help="Path to save the result JSON", default=CANVAS_RESULT_FILE)

    args = parser.parse_args()

    try:
        executor = WorkflowExecutor()
        result = executor.execute_pipeline(args.workflow_file)

        # Save to specified result file
        if args.result_file != CANVAS_RESULT_FILE:
            with open(args.result_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Saved results to {args.result_file}")

        logger.info("Workflow execution completed successfully")
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
