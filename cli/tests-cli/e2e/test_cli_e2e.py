"""E2E: CLI against an engine you start separately (CI sets ENGINE_URL; local: run engine or Docker).

Tests that call ``run`` need a reachable engine at ENGINE_URL (default http://localhost:8080).
"""

import subprocess
import sys
import os

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CLI_SCRIPT = os.path.join(BASE_DIR, "cli", "sawectl.py")
MODULES_DIR = os.path.join(BASE_DIR, "engine", "modules")
SAMPLES_DIR = os.path.join(BASE_DIR, "engine", "workflows", "samples")

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8080")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, CLI_SCRIPT, *args],
        capture_output=True, text=True
    )


def _engine_reachable():
    try:
        r = requests.get(ENGINE_URL, timeout=2)
        return r.status_code in (200, 404)
    except requests.RequestException:
        return False


class TestCli:
    """E2E: Verify the CLI; engine must already be running for run tests."""

    def test_cli_validates_before_sending(self):
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("validate-workflow", "--workflow", workflow, "--modules", MODULES_DIR)
        assert result.returncode == 0
        assert "VALIDATION PASSED" in result.stdout

    def test_cli_run_triggers_workflow(self):
        assert _engine_reachable(), f"No engine at {ENGINE_URL} — start it or set ENGINE_URL"
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        server = ENGINE_URL.replace("http://", "").replace("https://", "")
        result = run_cli("run", "--workflow", workflow, "--server", server)
        assert "triggered" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_cli_run_bad_server_fails(self):
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("run", "--workflow", workflow, "--server", "localhost:9999")
        assert result.returncode != 0
        assert "error" in result.stdout.lower() or "error" in result.stderr.lower()
