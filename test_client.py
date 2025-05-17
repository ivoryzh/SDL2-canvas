import requests
import time
import json
import uuid
from typing import Dict, Any, Optional

# Base URL for the API
BASE_URL = "http://localhost:8000"


def print_json(data: Dict[str, Any]) -> None:
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))


def create_cv_task() -> Dict[str, Any]:
    """Create a CV task and return the response data"""
    endpoint = f"{BASE_URL}/tasks/cv/"

    # Sample CV task parameters
    payload = {
        "v_range": [-0.5, 0.5],  # Voltage range in V
        "freq": 0.1,  # Frequency in Hz
    }

    response = requests.post(endpoint, json=payload)
    response.raise_for_status()  # Raise exception for HTTP errors

    return response.json()


def get_task_status(task_id: uuid.UUID) -> Dict[str, Any]:
    """Get the status of a task by its ID"""
    endpoint = f"{BASE_URL}/task/{task_id}"

    response = requests.get(endpoint)
    response.raise_for_status()

    return response.json()


def wait_for_task_completion(
    task_id: uuid.UUID, check_interval: int = 5
) -> Dict[str, Any]:
    """
    Poll the API until the task is completed.

    Args:
        task_id: The ID of the task to check
        check_interval: How often to check the status in seconds

    Returns:
        The completed task data
    """
    print(f"Waiting for task {task_id} to complete...")

    while True:
        task_data = get_task_status(task_id)
        status = task_data["status"]

        print(f"Current status: {status}")

        if status == 1:  # COMPLETED
            print("Task completed successfully!")
            return task_data
        elif status == 3:  # ERROR
            raise Exception(f"Task failed with error status")
        elif status == 0 or status == 2:  # PENDING or RUNNING
            # Wait before checking again
            time.sleep(check_interval)
        else:
            raise Exception(f"Unknown task status: {status}")


def extract_csv_id(task_data: Dict[str, Any]) -> Optional[uuid.UUID]:
    """Extract the CSV ID from a completed task"""
    if task_data.get("output") and task_data["output"].get("id"):
        return task_data["output"]["id"]
    return None


def create_rolling_mean_task(csv_id: uuid.UUID) -> Dict[str, Any]:
    """Create a rolling mean task using a CSV ID and return the response data"""
    endpoint = f"{BASE_URL}/tasks/rolling_mean/"

    # Sample rolling mean parameters
    payload = {
        "csv_id": str(csv_id),
        "x_col": "time",
        "y_col": "current",
        "window_size": 20,
    }

    response = requests.post(endpoint, json=payload)
    response.raise_for_status()

    return response.json()


def create_peak_detection_task(csv_id: uuid.UUID) -> Dict[str, Any]:
    """Create a peak detection task using a CSV ID and return the response data"""
    endpoint = f"{BASE_URL}/tasks/peak_detection/"

    # Sample peak detection parameters
    payload = {
        "csv_id": str(csv_id),
        "x_col": "voltage",
        "y_col": "current",
        "height": 0.05,  # Minimum peak height
        "prominence": 0.02,  # Minimum peak prominence
        "distance": 10,  # Minimum horizontal distance between peaks
        "width": None,  # Minimum peak width (not specified)
        "threshold": 0.01,  # Required threshold for detection
    }

    response = requests.post(endpoint, json=payload)
    response.raise_for_status()

    return response.json()


def main():
    # Step 1: Create and execute a CV task
    print("\n----- STEP 1: Creating CV task -----")
    cv_task = create_cv_task()
    print_json(cv_task)

    # Get the task ID
    cv_task_id = cv_task["id"]

    # Step 2: Wait for the CV task to complete
    print("\n----- STEP 2: Waiting for CV task to complete -----")
    completed_cv_task = wait_for_task_completion(cv_task_id)
    print("CV task completed with data:")
    print_json(completed_cv_task)

    # Step 3: Extract the CSV ID from the completed CV task
    print("\n----- STEP 3: Extracting CSV data -----")
    csv_id = extract_csv_id(completed_cv_task)
    if not csv_id:
        raise Exception("Could not extract CSV ID from the completed CV task")

    print(f"Extracted CSV ID: {csv_id}")

    # Step 4: Create a rolling mean task using the CSV ID
    print("\n----- STEP 4: Creating rolling mean task -----")
    rolling_task = create_rolling_mean_task(csv_id)
    print_json(rolling_task)

    # Step 5: Wait for the rolling mean task to complete
    print("\n----- STEP 5: Waiting for rolling mean task to complete -----")
    rolling_task_id = rolling_task["id"]
    completed_rolling_task = wait_for_task_completion(rolling_task_id)

    print("Rolling mean task completed with data:")
    print_json(completed_rolling_task)

    # Step 6: Extract the processed CSV ID from the rolling mean task
    print("\n----- STEP 6: Extracting processed CSV data -----")
    processed_csv_id = extract_csv_id(completed_rolling_task)
    if not processed_csv_id:
        raise Exception("Could not extract CSV ID from the completed rolling mean task")
    print(f"Processed CSV ID: {processed_csv_id}")

    # Step 7: Create a peak detection task using the processed CSV ID
    print("\n----- STEP 7: Creating peak detection task -----")
    peak_detection_task = create_peak_detection_task(processed_csv_id)
    print_json(peak_detection_task)

    # Step 8: Wait for the peak detection task to complete
    print("\n----- STEP 8: Waiting for peak detection task to complete -----")
    peak_detection_task_id = peak_detection_task["id"]
    completed_peak_detection_task = wait_for_task_completion(peak_detection_task_id)

    print("Peak detection task completed with data:")
    print_json(completed_peak_detection_task)

    # Step 9: Extract the peaks CSV ID if needed
    print("\n----- STEP 9: Extracting peaks data -----")
    peaks_csv_id = extract_csv_id(completed_peak_detection_task)
    if peaks_csv_id:
        print(f"Peaks CSV ID: {peaks_csv_id}")

    print("\nComplete workflow executed successfully!")


if __name__ == "__main__":
    main()
