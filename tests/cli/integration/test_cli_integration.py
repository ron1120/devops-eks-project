import subprocess
import os
import sys
import shutil

# Base paths — go up from tests/cli/integration/ to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CLI_SCRIPT = os.path.join(BASE_DIR, "cli", "sawectl.py")
MODULES_DIR = os.path.join(BASE_DIR, "modules")
SAMPLES_DIR = os.path.join(BASE_DIR, "workflows", "samples")


def run_cli(*args):
    """Helper to run the CLI and return the result."""
    result = subprocess.run(
        [sys.executable, CLI_SCRIPT, *args],
        capture_output=True,
        text=True
    )
    return result


class TestCLIValidateWorkflow:
    """Integration tests: CLI validates real workflow YAML files against real module manifests."""

    def test_validate_valid_workflow(self):
        """Test that the CLI successfully validates a correct sample workflow."""
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("validate-workflow", "--workflow", workflow, "--modules", MODULES_DIR)
        assert result.returncode == 0
        assert "VALIDATION PASSED" in result.stdout

    def test_validate_workflow_verbose(self):
        """Test that verbose flag prints per-step validation details."""
        workflow = os.path.join(SAMPLES_DIR, "command_and_slack.yaml")
        result = run_cli("validate-workflow", "--workflow", workflow, "--modules", MODULES_DIR, "--verbose")
        assert result.returncode == 0
        assert "[OK]" in result.stdout

    def test_validate_nonexistent_workflow_file(self):
        """Test that CLI fails gracefully when given a non-existent workflow file."""
        result = run_cli("validate-workflow", "--workflow", "/tmp/nonexistent_workflow.yaml", "--modules", MODULES_DIR)
        assert result.returncode != 0
        assert "ERROR" in result.stdout or "error" in result.stderr.lower()


class TestCLIValidateModules:
    """Integration tests: CLI validates real module manifests on disk."""

    def test_validate_all_modules(self):
        """Test that all module manifests pass validation."""
        result = run_cli("validate-modules", "--modules", MODULES_DIR)
        assert result.returncode == 0
        assert "All module manifests passed validation" in result.stdout

    def test_validate_modules_nonexistent_dir(self):
        """Test that CLI fails gracefully with a bad modules directory."""
        result = run_cli("validate-modules", "--modules", "/tmp/fake_modules_dir")
        assert result.returncode != 0


class TestCLIInitWorkflow:
    """Integration tests: CLI generates a workflow from real schemas and modules."""

    def test_init_workflow_full(self):
        """Test that the CLI can generate a full workflow YAML from existing modules."""
        result = run_cli("init", "workflow", "test_wf", "--full", "--modules-path", MODULES_DIR)
        assert result.returncode == 0

    def test_init_workflow_minimal(self):
        """Test that the CLI can generate a minimal workflow."""
        result = run_cli("init", "workflow", "test_minimal_wf", "--minimal")
        assert result.returncode == 0


class TestCLIInitModule:
    """Integration tests: CLI scaffolds a new module on disk."""

    def test_init_module_creates_files(self):
        """Test that init module creates the expected skeleton files."""
        module_name = "test_scaffold_module"
        module_path = os.path.join(MODULES_DIR, module_name)

        # Clean up if leftover from a previous run
        if os.path.exists(module_path):
            shutil.rmtree(module_path)

        result = subprocess.run(
            [sys.executable, CLI_SCRIPT, "init", "module", module_name],
            capture_output=True, text=True,
            cwd=BASE_DIR
        )
        assert result.returncode == 0
        assert os.path.isdir(module_path)
        assert os.path.isfile(os.path.join(module_path, "module.yaml"))
        assert os.path.isfile(os.path.join(module_path, f"{module_name}.py"))
        assert os.path.isfile(os.path.join(module_path, "usage_reference.yaml"))

        # Clean up
        shutil.rmtree(module_path)
