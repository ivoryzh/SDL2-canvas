"""
SDL2 API Client for interacting with the SDL2 API endpoints.
"""
import time
import json
import logging
import uuid
from typing import Dict, Any, Optional, Union, List
import requests
from config import SDL2_API_BASE_URL, TASK_POLL_INTERVAL_SECONDS, TASK_MAX_WAIT_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sdl2_client")


class SDL2Client:
    """Client for interacting with the SDL2 API."""
    
    def __init__(self, base_url: str = SDL2_API_BASE_URL):
        """
        Initialize the SDL2 client.
        
        Args:
            base_url: Base URL for the SDL2 API
        """
        self.base_url = base_url
        logger.info(f"Initialized SDL2 client with base URL: {base_url}")
    
    def create_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task in SDL2.
        
        Args:
            task_type: Type of task (cv, rolling_mean, peak_detection, etc.)
            payload: Task parameters
            
        Returns:
            Task data including the task ID
        """
        endpoint = f"{self.base_url}/tasks/{task_type}/"
        
        logger.info(f"Creating {task_type} task with payload: {payload}")
        
        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            task_data = response.json()
            logger.info(f"Created task with ID: {task_data['id']}")
            return task_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating task: {str(e)}")
            raise
    
    def get_task_status(self, task_id: Union[uuid.UUID, str]) -> Dict[str, Any]:
        """
        Get the status of a task by its ID.
        
        Args:
            task_id: The ID of the task to check
            
        Returns:
            Task data including status
        """
        endpoint = f"{self.base_url}/task/{task_id}"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting task status: {str(e)}")
            raise
    
    def wait_for_task_completion(
        self, 
        task_id: Union[uuid.UUID, str], 
        check_interval: int = TASK_POLL_INTERVAL_SECONDS,
        max_wait_seconds: int = TASK_MAX_WAIT_SECONDS
    ) -> Dict[str, Any]:
        """
        Poll the API until the task is completed or timeout is reached.
        
        Args:
            task_id: The ID of the task to check
            check_interval: How often to check the status in seconds
            max_wait_seconds: Maximum time to wait in seconds
            
        Returns:
            The completed task data
            
        Raises:
            TimeoutError: If the task doesn't complete within max_wait_seconds
            Exception: If the task fails with an error status
        """
        logger.info(f"Waiting for task {task_id} to complete...")
        
        start_time = time.time()
        
        while True:
            # Check if we've exceeded the maximum wait time
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_seconds:
                raise TimeoutError(f"Task {task_id} did not complete within {max_wait_seconds} seconds")
            
            task_data = self.get_task_status(task_id)
            status = task_data["status"]
            
            logger.debug(f"Current status: {status}")
            
            if status == 1:  # COMPLETED
                logger.info(f"Task {task_id} completed successfully!")
                return task_data
            elif status == 3:  # ERROR
                error_msg = f"Task {task_id} failed with error status"
                logger.error(error_msg)
                raise Exception(error_msg)
            elif status == 0 or status == 2:  # PENDING or RUNNING
                # Wait before checking again
                time.sleep(check_interval)
            else:
                error_msg = f"Unknown task status: {status}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    def get_csv_data(self, csv_id: Union[uuid.UUID, str]) -> Dict[str, Any]:
        """
        Get CSV data by its ID.
        
        Args:
            csv_id: The ID of the CSV data to retrieve
            
        Returns:
            CSV data
        """
        endpoint = f"{self.base_url}/csv/{csv_id}"
        
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting CSV data: {str(e)}")
            raise
    
    def extract_csv_id(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract the CSV ID from a completed task.
        
        Args:
            task_data: Task data from a completed task
            
        Returns:
            CSV ID or None if not found
        """
        if task_data.get("output") and task_data["output"].get("id"):
            return task_data["output"]["id"]
        return None
