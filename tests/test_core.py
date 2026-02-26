import pytest
from unittest.mock import patch, MagicMock
from src.core.process import log_crash, shutdown_cleanup, init_crash_logging
from src.core.errors import handle_fatal_error
import sys


def test_init_crash_logging_frozen(monkeypatch):
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.stdout", None)
    monkeypatch.setattr("sys.stderr", None)
    init_crash_logging()
    assert sys.stdout is not None
    assert sys.stderr is not None


@patch("builtins.open")
@patch("builtins.print")
def test_log_crash(mock_print, mock_open):
    log_crash(Exception("Test Crash"))
    mock_open.assert_called_once()
    assert mock_print.call_count >= 2


@patch("builtins.open")
@patch("builtins.print")
def test_log_crash_frozen(mock_print, mock_open, monkeypatch):
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", "/path/to/exe", raising=False)
    log_crash(Exception("Test Crash"))
    mock_open.assert_called_once()


@patch("builtins.open")
@patch("builtins.print")
def test_log_crash_open_fails(mock_print, mock_open):
    mock_open.side_effect = Exception("Disk Full")
    log_crash(Exception("Test Crash"))
    # Should print failure message
    mock_print.assert_any_call("Failed to write crash log: Disk Full")


@patch("psutil.Process")
def test_shutdown_cleanup(mock_process):
    # Setup mock process and children
    mock_proc_instance = MagicMock()
    mock_child = MagicMock()
    mock_child.pid = 123
    mock_proc_instance.children.return_value = [mock_child]
    mock_process.return_value = mock_proc_instance

    # Mock wait_procs to return empty alive list
    with patch("psutil.wait_procs", return_value=([], [])):
        logger_mock = MagicMock()
        shutdown_cleanup(logger_mock)
        mock_child.terminate.assert_called_once()


@patch("src.core.errors.log_crash")
def test_handle_fatal_error_system_exit(mock_log):
    # Should exit 0 without logging crash
    with pytest.raises(SystemExit) as e:
        handle_fatal_error(SystemExit(0))
    assert e.value.code == 0
    mock_log.assert_not_called()


@patch("src.core.errors.log_crash")
@patch("builtins.print")
def test_handle_fatal_error_exception(mock_print, mock_log_crash, monkeypatch):
    monkeypatch.setattr("sys.frozen", False, raising=False)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False, raising=False)

    with pytest.raises(SystemExit) as e:
        handle_fatal_error(Exception("Fatal Base Exception"))

    assert e.value.code == 1
    mock_log_crash.assert_called_once()
    mock_print.assert_called()
