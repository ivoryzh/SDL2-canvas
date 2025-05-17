import pytest
import pandas as pd
import numpy as np
from data_process import rolling_mean, detect_peaks

def test_rolling_mean():
    """Test rolling mean calculation."""
    # Create test data
    data = pd.DataFrame({
        'time': np.arange(10),
        'current': np.sin(np.arange(10))
    })
    
    # Calculate rolling mean
    result = rolling_mean(
        data,
        x_col='time',
        y_col='current',
        window_size=3,
        min_periods=1
    )
    
    assert isinstance(result, pd.DataFrame)
    assert 'time' in result.columns
    assert 'current' in result.columns
    assert len(result) == len(data)
    assert not result['current'].isnull().any()

def test_peak_detection():
    """Test peak detection."""
    # Create test data with known peaks
    x = np.linspace(0, 10, 100)
    y = np.sin(x) + 0.5 * np.sin(2 * x)
    data = pd.DataFrame({
        'voltage': x,
        'current': y
    })
    
    # Detect peaks
    peaks = detect_peaks(
        data,
        x_col='voltage',
        y_col='current',
        height=0.5,
        prominence=0.2,
        distance=10,
        threshold=0.1
    )
    
    assert isinstance(peaks, pd.DataFrame)
    assert 'voltage' in peaks.columns
    assert 'current' in peaks.columns
    assert len(peaks) > 0

def test_rolling_mean_with_invalid_data():
    """Test rolling mean with invalid data."""
    # Create invalid data
    data = pd.DataFrame({
        'time': [1, 2, 3, np.nan, 5],
        'current': [0.1, 0.2, np.nan, 0.4, 0.5]
    })
    
    with pytest.raises(ValueError):
        rolling_mean(
            data,
            x_col='time',
            y_col='current',
            window_size=3
        )

def test_peak_detection_with_no_peaks():
    """Test peak detection with data containing no peaks."""
    # Create flat data
    data = pd.DataFrame({
        'voltage': np.linspace(0, 10, 100),
        'current': np.ones(100)
    })
    
    peaks = detect_peaks(
        data,
        x_col='voltage',
        y_col='current',
        height=0.5,
        prominence=0.2
    )
    
    assert isinstance(peaks, pd.DataFrame)
    assert len(peaks) == 0

def test_rolling_mean_parameters():
    """Test rolling mean with different parameters."""
    # Create test data
    data = pd.DataFrame({
        'time': np.arange(10),
        'current': np.sin(np.arange(10))
    })
    
    # Test different window sizes
    for window_size in [2, 3, 5]:
        result = rolling_mean(
            data,
            x_col='time',
            y_col='current',
            window_size=window_size
        )
        assert len(result) == len(data)
    
    # Test different min_periods
    for min_periods in [1, 2, 3]:
        result = rolling_mean(
            data,
            x_col='time',
            y_col='current',
            window_size=3,
            min_periods=min_periods
        )
        assert len(result) == len(data)

def test_peak_detection_parameters():
    """Test peak detection with different parameters."""
    # Create test data
    x = np.linspace(0, 10, 100)
    y = np.sin(x) + 0.5 * np.sin(2 * x)
    data = pd.DataFrame({
        'voltage': x,
        'current': y
    })
    
    # Test different height thresholds
    for height in [0.3, 0.5, 0.7]:
        peaks = detect_peaks(
            data,
            x_col='voltage',
            y_col='current',
            height=height
        )
        assert isinstance(peaks, pd.DataFrame)
    
    # Test different prominence values
    for prominence in [0.1, 0.2, 0.3]:
        peaks = detect_peaks(
            data,
            x_col='voltage',
            y_col='current',
            prominence=prominence
        )
        assert isinstance(peaks, pd.DataFrame) 