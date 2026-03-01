import sys
from unittest.mock import MagicMock, patch

import pytest

from src.core.errors import handle_fatal_error
from src.core.process import init_crash_logging, log_crash, shutdown_cleanup


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


@patch("subprocess.Popen")
@patch("psutil.Process")
def test_shutdown_cleanup(mock_process, mock_popen):
    import src.core.process as proc_module

    # Reset the guard flag so the test can run
    proc_module._cleanup_done = False

    # Setup mock: current process with a parent of different name (no tree walk)
    mock_current = MagicMock()
    mock_current.pid = 100
    mock_current.name.return_value = "TodoApp.exe"

    mock_parent = MagicMock()
    mock_parent.pid = 50
    mock_parent.name.return_value = "explorer.exe"

    mock_current.parent.return_value = mock_parent
    mock_process.return_value = mock_current

    logger_mock = MagicMock()
    shutdown_cleanup(logger_mock)

    # Should call taskkill with the root PID (current, since parent has different name)
    mock_popen.assert_called_once()
    call_args = mock_popen.call_args[0][0]
    assert call_args[:4] == ["taskkill", "/F", "/T", "/PID"]
    assert call_args[4] == "100"


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
