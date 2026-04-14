"""E2E: HTTP checks against an engine you start separately (CI sets ENGINE_URL).

Default ENGINE_URL is http://localhost:8080 — run the engine (or container) before pytest.
"""

import os

import requests

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8080")
ENGINE_ADHOC = f"{ENGINE_URL}/api/adhoc"


class TestEngine:
    """E2E: Engine must already be running at ENGINE_URL."""

    def test_engine_is_listening(self):
        try:
            resp = requests.get(ENGINE_URL, timeout=3)
            assert resp.status_code in [200, 404]
        except requests.ConnectionError:
            assert False, f"Engine is not reachable at {ENGINE_URL}"

    def test_engine_adhoc_endpoint_exists(self):
        resp = requests.post(ENGINE_ADHOC, json={"workflow": {}}, timeout=3)
        assert resp.status_code != 405, "POST /api/adhoc returned Method Not Allowed"
