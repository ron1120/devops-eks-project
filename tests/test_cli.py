import subprocess
import os

def test_cli_help():
    """Test that the CLI runs and returns the help menu successfully."""
    # Get the absolute path to the CLI script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cli_script = os.path.join(base_dir, "cli", "sawectl.py")
    
    # Run the script with --help
    result = subprocess.run(
        ["python", cli_script, "--help"], 
        capture_output=True, 
        text=True
    )
    
    # Assert the command ran successfully (exit code 0)
    assert result.returncode == 0
    # Assert that some expected output was printed (help text usually contains 'usage:' or 'help')
    assert "usage:" in result.stdout.lower() or "help" in result.stdout.lower()
