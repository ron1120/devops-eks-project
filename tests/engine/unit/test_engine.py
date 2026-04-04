import os
import subprocess

def test_engine_binary_exists():
    """Test that the engine executable for the current platform exists."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # We will test the macOS ARM binary since the current OS is macOS
    engine_bin = os.path.join(base_dir, "engine", "seyoawe.macos.arm")
    
    assert os.path.exists(engine_bin), f"Engine binary not found at {engine_bin}"
    assert os.access(engine_bin, os.X_OK), "Engine binary is not executable"

def test_engine_run_sh_help():
    """Test that the engine run.sh script returns the usage text when run without arguments."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_script = os.path.join(base_dir, "engine", "run.sh")
    
    result = subprocess.run(
        ["bash", run_script], 
        capture_output=True, 
        text=True
    )
    
    # Assert it fails with usage text or exits non-zero
    assert result.returncode != 0
    assert "Usage:" in result.stdout.lower() or "Usage:" in result.stderr.lower() or "linux" in result.stdout.lower()
