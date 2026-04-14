import os
import time
import signal
import subprocess
import platform
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")

BINARY_NAME = "seyoawe.linux" if platform.system() == "Linux" else "seyoawe.macos.arm"
ENGINE_BIN = os.path.join(ENGINE_DIR, BINARY_NAME)

EXTERNAL_ENGINE = "ENGINE_URL" in os.environ
ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8080")
ENGINE_ADHOC = f"{ENGINE_URL}/api/adhoc"


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


class TestEngine:
    """E2E: Verify the engine is reachable and responds correctly."""

    @classmethod
    def setup_class(cls):
        cls.engine_proc = None if EXTERNAL_ENGINE else start_engine()

    @classmethod
    def teardown_class(cls):
        if cls.engine_proc:
            stop_engine(cls.engine_proc)

    def test_engine_is_listening(self):
        try:
            resp = requests.get(ENGINE_URL, timeout=3)
            assert resp.status_code in [200, 404]
        except requests.ConnectionError:
            assert False, f"Engine is not reachable at {ENGINE_URL}"

    def test_engine_adhoc_endpoint_exists(self):
        resp = requests.post(ENGINE_ADHOC, json={"workflow": {}}, timeout=3)
        assert resp.status_code != 405, "POST /api/adhoc returned Method Not Allowed"
