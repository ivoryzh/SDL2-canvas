import pytest
import json
from pathlib import Path
from src.core.workflow_executor import WorkflowExecutor

def test_simple_cv_workflow(test_workflow_data, tmp_path):
    """Test executing a simple CV workflow."""
    # Create a temporary workflow file
    workflow_file = tmp_path / "test_workflow.json"
    workflow_file.write_text(json.dumps(test_workflow_data))
    
    # Execute workflow
    executor = WorkflowExecutor()
    result = executor.execute_pipeline(str(workflow_file))
    
    assert result is not None
    assert "operations" in result
    assert len(result["operations"]) == 1
    assert result["operations"][0]["id"] == "test_cv"

def test_data_processing_workflow(tmp_path):
    """Test executing a data processing workflow."""
    workflow_data = {
        "name": "Test_Data_Processing",
        "description": "Test workflow with multiple operations",
        "operations": [
            {
                "id": "cv_operation",
                "type": "uo_sdl2_cv",
                "params": {
                    "v_range": [-0.5, 0.5],
                    "freq": 0.1
                }
            },
            {
                "id": "rolling_mean",
                "type": "uo_sdl2_rolling_mean",
                "params": {
                    "csv_id": "$cv_operation.output.id",
                    "x_col": "time",
                    "y_col": "current",
                    "window_size": 20
                }
            },
            {
                "id": "peak_detection",
                "type": "uo_sdl2_peak_detection",
                "params": {
                    "csv_id": "$rolling_mean.output.id",
                    "x_col": "voltage",
                    "y_col": "current",
                    "height": 0.05,
                    "prominence": 0.02,
                    "distance": 10,
                    "threshold": 0.01
                }
            }
        ]
    }
    
    # Create a temporary workflow file
    workflow_file = tmp_path / "test_workflow.json"
    workflow_file.write_text(json.dumps(workflow_data))
    
    # Execute workflow
    executor = WorkflowExecutor()
    result = executor.execute_pipeline(str(workflow_file))
    
    assert result is not None
    assert "operations" in result
    assert len(result["operations"]) == 3
    assert result["operations"][0]["id"] == "cv_operation"
    assert result["operations"][1]["id"] == "rolling_mean"
    assert result["operations"][2]["id"] == "peak_detection"

def test_invalid_workflow(tmp_path):
    """Test handling of invalid workflow."""
    invalid_workflow = {
        "name": "Invalid_Workflow",
        "description": "Workflow with invalid operation type",
        "operations": [
            {
                "id": "invalid_operation",
                "type": "invalid_type",
                "params": {}
            }
        ]
    }
    
    # Create a temporary workflow file
    workflow_file = tmp_path / "invalid_workflow.json"
    workflow_file.write_text(json.dumps(invalid_workflow))
    
    # Execute workflow
    executor = WorkflowExecutor()
    with pytest.raises(Exception):
        executor.execute_pipeline(str(workflow_file))

def test_workflow_with_missing_dependency(tmp_path):
    """Test handling of workflow with missing dependency."""
    workflow_data = {
        "name": "Test_Missing_Dependency",
        "description": "Workflow with missing operation dependency",
        "operations": [
            {
                "id": "rolling_mean",
                "type": "uo_sdl2_rolling_mean",
                "params": {
                    "csv_id": "$nonexistent_operation.output.id",
                    "x_col": "time",
                    "y_col": "current",
                    "window_size": 20
                }
            }
        ]
    }
    
    # Create a temporary workflow file
    workflow_file = tmp_path / "test_workflow.json"
    workflow_file.write_text(json.dumps(workflow_data))
    
    # Execute workflow
    executor = WorkflowExecutor()
    with pytest.raises(Exception):
        executor.execute_pipeline(str(workflow_file)) 