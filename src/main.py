#!/usr/bin/env python3
"""
Main entry point for SDL2 Canvas Integration.
"""
import os
import sys
import logging
import argparse
from src.core.workflow_executor import WorkflowExecutor
from src.utils.config import CANVAS_RESULT_FILE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="SDL2 Canvas Integration")
    parser.add_argument("workflow_file", help="Path to the workflow JSON file")
    parser.add_argument("--result-file", help="Path to save the result JSON", default=CANVAS_RESULT_FILE)
    parser.add_argument("--log-level", help="Logging level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        # Check if workflow file exists
        if not os.path.isfile(args.workflow_file):
            logger.error(f"Workflow file not found: {args.workflow_file}")
            return 1

        # Execute workflow
        executor = WorkflowExecutor()
        result = executor.execute_pipeline(args.workflow_file)

        # Save to specified result file
        if args.result_file != CANVAS_RESULT_FILE:
            executor.save_results(args.result_file)

        logger.info("Workflow execution completed successfully")
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
