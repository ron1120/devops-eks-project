import os
import subprocess

# Go up from engine/tests-engine/unit/ to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
RUN_SCRIPT = os.path.join(ENGINE_DIR, "run.sh")


# --------- Binaries ---------

def test_engine_macos_binary_exists():
    """Test that the macOS ARM binary exists and is executable."""
    engine_bin = os.path.join(ENGINE_DIR, "seyoawe.macos.arm")
    assert os.path.exists(engine_bin)
    assert os.access(engine_bin, os.X_OK)

def test_engine_linux_binary_exists():
    """Test that the Linux binary exists and is executable."""
    engine_bin = os.path.join(ENGINE_DIR, "seyoawe.linux")
    assert os.path.exists(engine_bin)
    assert os.access(engine_bin, os.X_OK)


# --------- run.sh ---------

def test_run_sh_exists():
    """Test that run.sh exists and is readable."""
    assert os.path.isfile(RUN_SCRIPT)

def test_run_sh_no_args_shows_usage():
    """Test that run.sh without arguments prints usage and exits non-zero."""
    result = subprocess.run(["bash", RUN_SCRIPT], capture_output=True, text=True)
    assert result.returncode != 0
    assert "usage" in result.stdout.lower()

def test_run_sh_invalid_arg_fails():
    """Test that run.sh rejects an invalid argument."""
    result = subprocess.run(["bash", RUN_SCRIPT, "windows"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "invalid" in result.stdout.lower()


# --------- Directory structure ---------

def test_engine_has_required_directories():
    """Test that the engine ships with modules/, workflows/, and configuration/."""
    for dirname in ["modules", "workflows", "configuration"]:
        assert os.path.isdir(os.path.join(ENGINE_DIR, dirname)), f"Missing {dirname}/"

def test_config_file_exists():
    """Test that the engine config.yaml is present."""
    assert os.path.isfile(os.path.join(ENGINE_DIR, "configuration", "config.yaml"))
