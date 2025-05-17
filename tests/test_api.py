import pytest
from uuid import UUID
from fastapi.testclient import TestClient

def test_create_cv_task(test_client: TestClient):
    """Test creating a CV task."""
    response = test_client.post(
        "/tasks/cv/",
        json={
            "v_range": [-0.5, 0.5],
            "freq": 0.1
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "CV"
    assert data["status"] == "PENDING"

def test_create_rolling_mean_task(test_client: TestClient):
    """Test creating a rolling mean task."""
    # First create a CV task to get a valid csv_id
    cv_response = test_client.post(
        "/tasks/cv/",
        json={
            "v_range": [-0.5, 0.5],
            "freq": 0.1
        }
    )
    cv_data = cv_response.json()
    
    response = test_client.post(
        "/tasks/rolling_mean/",
        json={
            "csv_id": str(cv_data["id"]),
            "x_col": "time",
            "y_col": "current",
            "window_size": 20
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "ROLLING_MEAN"
    assert data["status"] == "PENDING"

def test_create_peak_detection_task(test_client: TestClient):
    """Test creating a peak detection task."""
    # First create a CV task to get a valid csv_id
    cv_response = test_client.post(
        "/tasks/cv/",
        json={
            "v_range": [-0.5, 0.5],
            "freq": 0.1
        }
    )
    cv_data = cv_response.json()
    
    response = test_client.post(
        "/tasks/peak_detection/",
        json={
            "csv_id": str(cv_data["id"]),
            "x_col": "voltage",
            "y_col": "current",
            "height": 0.05,
            "prominence": 0.02,
            "distance": 10,
            "threshold": 0.01
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "PEAK_DETECTION"
    assert data["status"] == "PENDING"

def test_get_task_status(test_client: TestClient):
    """Test getting task status."""
    # First create a task
    response = test_client.post(
        "/tasks/cv/",
        json={
            "v_range": [-0.5, 0.5],
            "freq": 0.1
        }
    )
    task_id = response.json()["id"]
    
    # Then get its status
    response = test_client.get(f"/task/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert "status" in data

def test_get_csv_data(test_client: TestClient):
    """Test getting CSV data."""
    # First create a CV task
    response = test_client.post(
        "/tasks/cv/",
        json={
            "v_range": [-0.5, 0.5],
            "freq": 0.1
        }
    )
    task_id = response.json()["id"]
    
    # Wait for task completion and get CSV ID
    # Note: In a real test, you might want to mock this or use a test database
    response = test_client.get(f"/task/{task_id}")
    csv_id = response.json().get("output", {}).get("id")
    
    if csv_id:
        response = test_client.get(f"/csv/{csv_id}")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data 