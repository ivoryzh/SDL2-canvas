# SDL2 Canvas Integration - Experiment Guide

This guide provides detailed instructions for setting up and running experiments with the SDL2 Canvas Integration system.

## System Requirements

### Software Requirements
- Python 3.8 or higher
- PostgreSQL 13 or higher
- SDL2 System
- Canvas System
- Git


## Installation Steps

### 1. Database Setup

#### PostgreSQL Installation
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

#### Database Configuration
```bash
# Create database and user
createdb sdl2
createuser -P dummy
# When prompted, set password to 'pass'

# Verify database connection
psql -d sdl2 -U dummy -h localhost
```

### 2. SDL2 System Setup

1. Install SDL2 system dependencies:
```bash
pip install -r requirements.txt
```

2. Configure SDL2 API:
```bash
# Copy example configuration
cp .env.example .env

# Edit .env file with your settings
nano .env
```

3. Start SDL2 API server:
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### 3. Canvas System Setup

1. Install Canvas system:
```bash
# Add Canvas installation steps here
```

2. Configure Canvas:
```bash
# Add Canvas configuration steps here
```

## Running Experiments

### 1. Basic Workflow

1. Start the SDL2 API server:
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

2. Run a simple CV workflow:
```bash
python run.py examples/cv_workflow.json
```

3. Check the results:
```bash
cat result.json
```

### 2. Advanced Workflow

1. Run a data processing workflow:
```bash
python run.py examples/data_processing_workflow.json --result-file output.json
```

2. Monitor the execution:
```bash
tail -f logs/app.log
```

## API Endpoints

### Task Creation Endpoints

1. Cyclic Voltammetry (CV)
```bash
curl -X POST http://localhost:8000/tasks/cv/ \
  -H "Content-Type: application/json" \
  -d '{
    "v_range": [-0.5, 0.5],
    "freq": 0.1
  }'
```

2. Rolling Mean
```bash
curl -X POST http://localhost:8000/tasks/rolling_mean/ \
  -H "Content-Type: application/json" \
  -d '{
    "csv_id": "previous_task_id",
    "x_col": "time",
    "y_col": "current",
    "window_size": 20
  }'
```

3. Peak Detection
```bash
curl -X POST http://localhost:8000/tasks/peak_detection/ \
  -H "Content-Type: application/json" \
  -d '{
    "csv_id": "previous_task_id",
    "x_col": "voltage",
    "y_col": "current",
    "height": 0.05,
    "prominence": 0.02,
    "distance": 10,
    "threshold": 0.01
  }'
```

### Task Status and Results

1. Check Task Status
```bash
curl http://localhost:8000/task/{task_id}
```

2. Get CSV Data
```bash
curl http://localhost:8000/csv/{csv_id}
```

## Troubleshooting

### Common Issues

1. Database Connection Errors
- Symptom: "Could not connect to database"
- Solution:
  ```bash
  # Check PostgreSQL service
  sudo service postgresql status
  
  # Verify database exists
  psql -l
  
  # Check connection settings in .env
  cat .env
  ```

2. API Connection Errors
- Symptom: "Connection refused"
- Solution:
  ```bash
  # Check if API server is running
  ps aux | grep uvicorn
  
  # Verify port availability
  netstat -tulpn | grep 8000
  ```

3. Workflow Execution Errors
- Symptom: "Invalid workflow JSON"
- Solution:
  ```bash
  # Validate JSON format
  python -m json.tool examples/cv_workflow.json
  
  # Check operation parameters
  cat examples/cv_workflow.json
  ```

### Logging

1. Application Logs
```bash
# View real-time logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log
```

2. Database Logs
```bash
# Ubuntu/Debian
tail -f /var/log/postgresql/postgresql-13-main.log

# macOS
tail -f /usr/local/var/log/postgres.log
```

## Data Management

### CSV Data Format

Required columns:
- `time`: Timestamp of measurement
- `voltage`: Applied voltage
- `current`: Measured current

### Data Storage

1. Raw Data
- Location: `data/raw/`
- Format: CSV files with timestamp prefix
- Naming: `YYYYMMDD_HHMMSS_experiment_name.csv`

2. Processed Data
- Location: `data/processed/`
- Format: CSV files with processing parameters
- Naming: `YYYYMMDD_HHMMSS_processed_experiment_name.csv`

### Data Cleanup

1. Automatic Cleanup
```bash
# Clean data older than 30 days
python scripts/cleanup.py --days 30
```

2. Manual Cleanup
```bash
# Remove specific experiment data
rm data/raw/YYYYMMDD_HHMMSS_experiment_name.csv
```

## Security

### API Authentication

1. Configure API Key
```bash
# In .env file
SDL2_API_KEY=your_secure_api_key
```

2. Use API Key in Requests
```bash
curl -X POST http://localhost:8000/tasks/cv/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secure_api_key" \
  -d '{
    "v_range": [-0.5, 0.5],
    "freq": 0.1
  }'
```

### Data Protection

1. Regular Backups
```bash
# Create backup
pg_dump -U dummy sdl2 > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U dummy sdl2 < backup_20240315.sql
```

2. Access Control
- Use strong passwords
- Limit database access to necessary users
- Regularly rotate API keys

## Best Practices

1. Experiment Planning
- Document experiment parameters
- Plan data storage requirements
- Consider backup needs

2. Workflow Design
- Start with simple workflows
- Test each operation individually
- Validate data dependencies

3. Data Management
- Regular backups
- Clear naming conventions
- Proper documentation

4. Security
- Regular password updates
- API key rotation
- Access log monitoring

## Support

For additional support:
1. Check the [documentation](docs/)
2. Review [example workflows](examples/)
3. Contact the development team

## Running Tests

### Test Setup

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Create test database:
```bash
createdb sdl2_test
```

### Running Tests

1. Run all tests:
```bash
pytest
```

2. Run specific test file:
```bash
pytest tests/test_api.py
```

3. Run tests with coverage report:
```bash
pytest --cov=src tests/
```

### Test Categories

1. API Tests (`tests/test_api.py`)
- Tests API endpoints
- Verifies task creation and status
- Checks data retrieval

2. Workflow Tests (`tests/test_workflow.py`)
- Tests workflow execution
- Verifies operation dependencies
- Checks error handling

3. Data Processing Tests (`tests/test_data_processing.py`)
- Tests data processing functions
- Verifies parameter handling
- Checks error cases

### Writing New Tests

1. Create a new test file in the `tests/` directory
2. Use the provided fixtures from `conftest.py`
3. Follow the existing test patterns
4. Add appropriate assertions

Example test structure:
```python
def test_new_feature():
    """Test description."""
    # Setup
    test_data = {...}
    
    # Execute
    result = function_to_test(test_data)
    
    # Assert
    assert result is not None
    assert result.expected_property == expected_value
```

### Test Best Practices

1. Test Organization
- Group related tests together
- Use descriptive test names
- Add clear docstrings

2. Test Data
- Use fixtures for common data
- Create minimal test cases
- Include edge cases

3. Assertions
- Test one thing per test
- Use specific assertions
- Check error conditions

4. Test Coverage
- Aim for high coverage
- Focus on critical paths
- Test error handling