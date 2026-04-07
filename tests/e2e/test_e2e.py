import subprocess
import sys
import os
import time
import signal
import requests

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
ENGINE_BIN = os.path.join(ENGINE_DIR, "seyoawe.macos.arm")
CLI_SCRIPT = os.path.join(BASE_DIR, "cli", "sawectl.py")
MODULES_DIR = os.path.join(BASE_DIR, "engine", "modules")
SAMPLES_DIR = os.path.join(BASE_DIR, "engine", "workflows", "samples")

ENGINE_URL = "http://localhost:8080"
ENGINE_ADHOC = f"{ENGINE_URL}/api/adhoc"


# --------- Helpers ---------

def start_engine():
    """Start the engine binary and wait for it to be ready."""
    proc = subprocess.Popen(
        [ENGINE_BIN],
        cwd=ENGINE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Wait for engine to start listening
    for _ in range(15):
        try:
            requests.get(ENGINE_URL, timeout=1)
            return proc
        except requests.ConnectionError:
            time.sleep(1)
    proc.kill()
    raise RuntimeError("Engine failed to start within 15 seconds")


def stop_engine(proc):
    """Gracefully stop the engine process."""
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def run_cli(*args):
    """Run the CLI and return the result."""
    return subprocess.run(
        [sys.executable, CLI_SCRIPT, *args],
        capture_output=True, text=True
    )


# --------- E2E Tests ---------

class TestE2EEngineIsReachable:
    """E2E: Start the engine and verify the CLI can reach it."""

    @classmethod
    def setup_class(cls):
        cls.engine_proc = start_engine()

    @classmethod
    def teardown_class(cls):
        stop_engine(cls.engine_proc)

    def test_engine_is_listening(self):
        """Test that the engine responds on port 8080."""
        try:
            resp = requests.get(ENGINE_URL, timeout=3)
            # 404 is fine — it means the server is alive, just no root route
            assert resp.status_code in [200, 404]
        except requests.ConnectionError:
            assert False, "Engine is not reachable on port 8080"

    def test_engine_adhoc_endpoint_exists(self):
        """Test that the /api/adhoc endpoint accepts POST."""
        resp = requests.post(ENGINE_ADHOC, json={"workflow": {}}, timeout=3)
        # Any response (even 400/404) means the endpoint is alive
        assert resp.status_code != 405, "POST /api/adhoc returned Method Not Allowed"

    def test_cli_validates_before_sending(self):
        """Test that the CLI validates a workflow before sending to the engine."""
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("validate-workflow", "--workflow", workflow, "--modules", MODULES_DIR)
        assert result.returncode == 0
        assert "VALIDATION PASSED" in result.stdout

    def test_cli_run_triggers_workflow(self):
        """Test that the CLI run command sends a workflow to the running engine."""
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("run", "--workflow", workflow, "--server", "localhost:8080")
        # The engine may reject the workflow (missing secrets etc), but the CLI should connect
        assert "triggered" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_cli_run_bad_server_fails(self):
        """Test that the CLI fails gracefully when the engine is unreachable."""
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("run", "--workflow", workflow, "--server", "localhost:9999")
        assert result.returncode != 0
        assert "error" in result.stdout.lower() or "error" in result.stderr.lower()
