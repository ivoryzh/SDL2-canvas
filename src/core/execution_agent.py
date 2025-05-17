"""
Execution Agent for SDL2 Canvas Integration.
"""
import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
from src.api.sdl2_client import SDL2Client
from src.operations.unit_operations import create_unit_operation
from src.utils.config import CANVAS_RESULT_FILE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("execution_agent")


class ExecutionAgent:
    """Agent for executing Canvas workflows with SDL2."""

    def __init__(self, client: Optional[SDL2Client] = None):
        """
        Initialize the execution agent.

        Args:
            client: SDL2 API client (optional, will create one if not provided)
        """
        self.client = client or SDL2Client()
        self.workflow = None
        self.results = {}

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

    def execute_workflow(self) -> Dict[str, Any]:
        """
        Execute the loaded workflow.

        Returns:
            Results of the workflow execution
        """
        if not self.workflow:
            raise ValueError("No workflow loaded. Call load_workflow first.")

        logger.info(f"Executing workflow: {self.workflow.get('name', 'Unnamed')}")

        # Extract workflow type and parameters
        workflow_type = self.workflow.get("type")
        params = self.workflow.get("params", {})

        if not workflow_type:
            raise ValueError("Workflow type not specified")

        # Create and execute the appropriate unit operation
        try:
            operation = create_unit_operation(workflow_type, params, self.client)
            result = operation.execute()

            # Save the result
            self.results = result

            # Save to result file
            self.save_results(CANVAS_RESULT_FILE)

            return result
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            raise

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
    """Main entry point for the execution agent."""
    parser = argparse.ArgumentParser(description="SDL2 Canvas Execution Agent")
    parser.add_argument("workflow_file", help="Path to the workflow JSON file")
    parser.add_argument("--result-file", help="Path to save the result JSON", default=CANVAS_RESULT_FILE)

    args = parser.parse_args()

    try:
        agent = ExecutionAgent()
        result = agent.execute_pipeline(args.workflow_file)

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
