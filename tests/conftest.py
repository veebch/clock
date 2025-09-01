"""Shared pytest fixtures for the test suite."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_machine_pin():
    """Mock machine.Pin for testing without hardware."""
    mock_instance = MagicMock()
    with patch.dict('sys.modules', {'machine': MagicMock()}):
        with patch('machine.Pin', return_value=mock_instance):
            yield mock_instance


@pytest.fixture
def mock_machine_rtc():
    """Mock machine.RTC for testing without hardware."""
    mock_instance = MagicMock()
    with patch.dict('sys.modules', {'machine': MagicMock()}):
        with patch('machine.RTC', return_value=mock_instance):
            yield mock_instance


@pytest.fixture
def mock_network():
    """Mock network module for testing without WiFi."""
    mock_instance = MagicMock()
    mock_instance.isconnected.return_value = True
    mock_instance.status.return_value = 3  # Connected status
    
    mock_network_module = MagicMock()
    mock_network_module.WLAN.return_value = mock_instance
    
    with patch.dict('sys.modules', {'network': mock_network_module}):
        yield mock_instance


@pytest.fixture
def mock_urequests():
    """Mock urequests for testing without network calls."""
    with patch('urequests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "year": 2023,
            "month": 12,
            "day": 25,
            "hour": 12,
            "minute": 30,
            "seconds": 45,
            "timeZone": "Australia/Canberra"
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_secrets():
    """Mock secrets module with test credentials."""
    mock_secrets_module = MagicMock()
    mock_secrets_module.WIFI_SSID = "test_ssid"
    mock_secrets_module.WIFI_PASSWORD = "test_password"
    
    with patch.dict('sys.modules', {'secrets': mock_secrets_module}):
        yield mock_secrets_module


@pytest.fixture
def mock_microdot():
    """Mock Microdot web framework for testing."""
    with patch('microdot.Microdot') as mock_app:
        mock_instance = MagicMock()
        mock_app.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_time_data():
    """Provide sample time data for testing."""
    return {
        "current_time": (2023, 12, 25, 12, 30, 45, 0, 0),
        "formatted": "2023-12-25 12:30:45",
        "epoch": 1703505045
    }


@pytest.fixture
def sample_dcf_signal():
    """Provide sample DCF77 signal data for testing."""
    return {
        "valid_signal": True,
        "time_data": "010011010101010101010101010101010101010101010101010101010101",
        "parity_ok": True,
        "signal_quality": 95
    }