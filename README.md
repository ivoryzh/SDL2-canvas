# SDL2 Canvas Integration

This repository implements the integration between SDL2 workflow and the Canvas system.

## Overview

The SDL2 Canvas Integration allows Canvas to act as a scheduler that triggers SDL2 endpoints. The workflow execution follows this pattern:

```
Canvas → Send configuration → SDL2 endpoint: /tasks/{task_type}/
                ↓
            Wait for results
                ↓
Canvas ← Receive results ← SDL2 endpoint: /task/{task_uuid}
                ↓
         Canvas updates experiment database state
```

## Components

- **Workflow Executor**: Parses Canvas workflow JSON and executes operations in sequence
- **SDL2 API Client**: Communicates with SDL2 API endpoints
- **Unit Operation Handlers**: Maps Canvas parameters to SDL2 API parameters
- **Data Management**: Handles data transfer between Canvas and SDL2

## Repository Structure

```
sdl2mock/
├── run.py                     # Entry point script
├── src/                       # Source code directory
│   ├── main.py                # Main application module
│   ├── api/                   # API client modules
│   │   └── sdl2_client.py     # SDL2 API client
│   ├── core/                  # Core functionality
│   │   ├── execution_agent.py # Simple execution agent
│   │   └── workflow_executor.py # Advanced workflow executor
│   ├── operations/            # Unit operation handlers
│   │   └── unit_operations.py # Unit operation implementations
│   └── utils/                 # Utility modules
│       ├── config.py          # Configuration settings
│       └── data_handler.py    # Data handling utilities
├── examples/                  # Example workflow JSON files
│   ├── cv_workflow.json
│   ├── peak_detection_workflow.json
│   └── data_processing_workflow.json
├── tests/                     # Test directory
├── docs/                      # Documentation
└── .env.example               # Example environment variables
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sdl2mock.git
   cd sdl2mock
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file to set the SDL2 API endpoint and other configuration options.

## Usage

### Basic Usage

Run a workflow using the entry point script:

```bash
python run.py examples/cv_workflow.json
```

This will:
1. Load the workflow JSON file
2. Execute the operations in sequence
3. Save the results to `result.json`

### Advanced Usage

You can specify a custom result file:

```bash
python run.py examples/data_processing_workflow.json --result-file output.json
```

You can also set the logging level:

```bash
python run.py examples/peak_detection_workflow.json --log-level DEBUG
```

## Workflow JSON Format

Workflows are defined in JSON format with the following structure:

```json
{
  "name": "Workflow_Name",
  "description": "Workflow description",
  "operations": [
    {
      "id": "operation_id",
      "type": "operation_type",
      "params": {
        "param1": "value1",
        "param2": "value2"
      }
    },
    {
      "id": "next_operation",
      "type": "next_operation_type",
      "params": {
        "param1": "$operation_id.output.some_field",
        "param2": "value2"
      }
    }
  ]
}
```

### Operation Types

The following operation types are supported:

- `uo_sdl2_cv`: Cyclic Voltammetry
- `uo_sdl2_rolling_mean`: Rolling Mean data processing
- `uo_sdl2_peak_detection`: Peak Detection data processing

### Parameter References

You can reference outputs from previous operations using the `$operation_id.output.field` syntax. This allows you to create workflows where operations depend on the results of previous operations.

## Example Workflows

### Simple CV Workflow

```json
{
  "name": "CV_Experiment",
  "description": "Simple cyclic voltammetry experiment",
  "operations": [
    {
      "id": "cv_operation",
      "type": "uo_sdl2_cv",
      "params": {
        "v_range": [-0.5, 0.5],
        "freq": 0.1
      }
    }
  ]
}
```

### Data Processing Workflow

```json
{
  "name": "Data_Processing_Workflow",
  "description": "Workflow that performs CV, rolling mean, and peak detection",
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
```

## Configuration

Configuration is managed through environment variables or the `.env` file:

- `SDL2_API_BASE_URL`: Base URL for the SDL2 API (default: http://localhost:8000)
- `TASK_POLL_INTERVAL_SECONDS`: How often to check task status (default: 5)
- `TASK_MAX_WAIT_SECONDS`: Maximum time to wait for task completion (default: 3600)
- `LOG_LEVEL`: Logging level (default: INFO)
- `CANVAS_RESULT_FILE`: Path to save the result JSON (default: result.json)

## Experiment Guide

For detailed instructions on setting up the experiment environment and running tests, please refer to [EXPERIMENT_GUIDE.md](EXPERIMENT_GUIDE.md).
