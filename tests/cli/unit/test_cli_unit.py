import subprocess
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CLI_SCRIPT = os.path.join(BASE_DIR, "cli", "sawectl.py")


def run_cli(*args):
    """Helper to run the CLI and return the result."""
    return subprocess.run(
        [sys.executable, CLI_SCRIPT, *args],
        capture_output=True, text=True
    )


# --------- Help ---------

def test_cli_help():
    """Test that --help returns successfully."""
    result = run_cli("--help")
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


# --------- Commands are recognized ---------

def test_validate_workflow_is_recognized():
    """Test that validate-workflow command exists (fails on missing args, not unknown command)."""
    result = run_cli("validate-workflow")
    assert "unknown command" not in result.stdout.lower()

def test_validate_modules_is_recognized():
    """Test that validate-modules command exists."""
    result = run_cli("validate-modules")
    assert "unknown command" not in result.stdout.lower()

def test_init_workflow_is_recognized():
    """Test that init workflow command exists."""
    result = run_cli("init", "workflow", "dummy")
    assert "unknown command" not in result.stdout.lower()

def test_init_module_is_recognized():
    """Test that init module command exists."""
    result = run_cli("init", "module", "dummy")
    assert "unknown command" not in result.stdout.lower()


# --------- Unknown command ---------

def test_unknown_command_fails():
    """Test that an unknown command returns a non-zero exit code."""
    result = run_cli("foobar")
    assert result.returncode != 0