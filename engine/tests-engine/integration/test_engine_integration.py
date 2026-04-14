import os
import yaml

# Base paths — go up from engine/tests-engine/integration/ to the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENGINE_DIR = os.path.join(BASE_DIR, "engine")
ENGINE_MODULES = os.path.join(ENGINE_DIR, "modules")
ENGINE_CONFIG = os.path.join(ENGINE_DIR, "configuration", "config.yaml")
ENGINE_WORKFLOWS = os.path.join(ENGINE_DIR, "workflows", "samples")


class TestEngineConfig:
    """Integration tests: Engine config is valid and references correct paths."""

    def test_config_file_is_valid_yaml(self):
        """Test that the engine config.yaml loads without errors."""
        with open(ENGINE_CONFIG) as f:
            config = yaml.safe_load(f)
        assert config is not None

    def test_config_has_required_sections(self):
        """Test that the config contains the essential top-level keys."""
        with open(ENGINE_CONFIG) as f:
            config = yaml.safe_load(f)
        assert "logging" in config
        assert "directories" in config
        assert "app" in config

    def test_config_port_is_set(self):
        """Test that the engine app port is configured."""
        with open(ENGINE_CONFIG) as f:
            config = yaml.safe_load(f)
        assert config["app"]["port"] is not None


class TestEngineModules:
    """Integration tests: Engine modules directory has valid module manifests."""

    def test_modules_directory_exists(self):
        """Test that the engine has a modules directory."""
        assert os.path.isdir(ENGINE_MODULES)

    def test_each_module_has_manifest(self):
        """Test that every standard module folder contains a module.yaml."""
        skip = {"webform"}  # webform is a special module without module.yaml
        for module in os.listdir(ENGINE_MODULES):
            module_path = os.path.join(ENGINE_MODULES, module)
            if os.path.isdir(module_path) and module not in skip:
                manifest = os.path.join(module_path, "module.yaml")
                assert os.path.isfile(manifest), f"Missing module.yaml in {module}"

    def test_each_manifest_has_required_fields(self):
        """Test that each module.yaml has name, class, and version."""
        for module in os.listdir(ENGINE_MODULES):
            module_path = os.path.join(ENGINE_MODULES, module)
            if os.path.isdir(module_path):
                manifest = os.path.join(module_path, "module.yaml")
                if os.path.isfile(manifest):
                    with open(manifest) as f:
                        data = yaml.safe_load(f)
                    assert "name" in data, f"{module}: missing 'name'"
                    assert "class" in data, f"{module}: missing 'class'"
                    assert "version" in data, f"{module}: missing 'version'"

    def test_each_module_has_python_file(self):
        """Test that every module folder has at least one .py file."""
        for module in os.listdir(ENGINE_MODULES):
            module_path = os.path.join(ENGINE_MODULES, module)
            if os.path.isdir(module_path):
                py_files = [f for f in os.listdir(module_path) if f.endswith(".py")]
                assert len(py_files) > 0, f"No .py file in {module}"


class TestEngineWorkflows:
    """Integration tests: Engine sample workflows are valid YAML."""

    def test_samples_directory_exists(self):
        """Test that the engine has sample workflows."""
        assert os.path.isdir(ENGINE_WORKFLOWS)

    def test_sample_workflows_are_valid_yaml(self):
        """Test that each sample workflow loads as valid YAML."""
        for filename in os.listdir(ENGINE_WORKFLOWS):
            if filename.endswith(".yaml"):
                filepath = os.path.join(ENGINE_WORKFLOWS, filename)
                with open(filepath) as f:
                    docs = list(yaml.safe_load_all(f))
                assert len(docs) > 0 and docs[0] is not None, f"{filename} is empty or invalid"
