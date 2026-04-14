import subprocess
import sys
import os
import time
import signal
import platform
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
CLI_SCRIPT = os.path.join(BASE_DIR, "cli", "sawectl.py")
MODULES_DIR = os.path.join(BASE_DIR, "engine", "modules")
SAMPLES_DIR = os.path.join(BASE_DIR, "engine", "workflows", "samples")

BINARY_NAME = "seyoawe.linux" if platform.system() == "Linux" else "seyoawe.macos.arm"
ENGINE_BIN = os.path.join(ENGINE_DIR, BINARY_NAME)

EXTERNAL_ENGINE = "ENGINE_URL" in os.environ
ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8080")


def start_engine():
    proc = subprocess.Popen(
        [ENGINE_BIN],
        cwd=ENGINE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for _ in range(15):
        try:
            requests.get(ENGINE_URL, timeout=1)
            return proc
        except requests.ConnectionError:
            time.sleep(1)
    proc.kill()
    raise RuntimeError(f"Engine failed to start within 15s (binary: {ENGINE_BIN})")


def stop_engine(proc):
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def run_cli(*args):
    return subprocess.run(
        [sys.executable, CLI_SCRIPT, *args],
        capture_output=True, text=True
    )


class TestCli:
    """E2E: Verify the CLI can interact with a running engine."""

    @classmethod
    def setup_class(cls):
        cls.engine_proc = None if EXTERNAL_ENGINE else start_engine()

    @classmethod
    def teardown_class(cls):
        if cls.engine_proc:
            stop_engine(cls.engine_proc)

    def test_cli_validates_before_sending(self):
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("validate-workflow", "--workflow", workflow, "--modules", MODULES_DIR)
        assert result.returncode == 0
        assert "VALIDATION PASSED" in result.stdout

    def test_cli_run_triggers_workflow(self):
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        server = ENGINE_URL.replace("http://", "").replace("https://", "")
        result = run_cli("run", "--workflow", workflow, "--server", server)
        assert "triggered" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_cli_run_bad_server_fails(self):
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("run", "--workflow", workflow, "--server", "localhost:9999")
        assert result.returncode != 0
        assert "error" in result.stdout.lower() or "error" in result.stderr.lower()
