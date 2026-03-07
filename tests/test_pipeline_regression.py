"""
API-free regression tests for SVG generation pipeline.

Confirms existing behavior of:
- Template loading and YAML parsing
- Purpose/mode classification constants
- Keyword-based purpose classification
- Template fallback behavior
- Module imports
"""

import pytest
import os
import yaml
from llm_client import (
    VALID_PURPOSES,
    VALID_MODES,
    load_template,
    load_all_templates,
    LLMClient,
)


class TestTemplateYAMLLoading:
    """Test that all YAML template files load correctly."""

    def test_all_template_yaml_files_load(self):
        """Load every YAML in /workspace/prompt_templates/ and validate structure."""
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "prompt_templates"
        )

        # Expected templates
        expected_templates = [
            "classic",
            "diagram",
            "icon",
            "infographic",
            "flat_illustration",
            "component",
        ]

        loaded_count = 0
        for template_name in expected_templates:
            yaml_path = os.path.join(templates_dir, f"{template_name}.yaml")

            # File should exist
            assert os.path.exists(yaml_path), (
                f"Template file {yaml_path} does not exist"
            )

            # Load and parse YAML
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Must parse without error
            assert data is not None, f"Template {template_name}.yaml parsed to None"

            # Must have system_prompt key
            assert "system_prompt" in data, (
                f"Template {template_name}.yaml missing 'system_prompt' key"
            )

            loaded_count += 1

        # Confirm we loaded all expected templates
        assert loaded_count == len(expected_templates), (
            f"Expected to load {len(expected_templates)} templates, "
            f"but only loaded {loaded_count}"
        )


class TestValidConstants:
    """Test that VALID_MODES and VALID_PURPOSES constants are correct."""

    def test_valid_modes_includes_all_expected(self):
        """Import VALID_MODES and verify it has correct values."""
        expected_modes = ["direct_svg", "code_generation", "component"]
        assert VALID_MODES == expected_modes, (
            f"VALID_MODES should be {expected_modes}, got {VALID_MODES}"
        )

    def test_valid_purposes_includes_all_expected(self):
        """Import VALID_PURPOSES and verify it has correct values."""
        expected_purposes = [
            "classic",
            "diagram",
            "icon",
            "infographic",
            "flat_illustration",
        ]
        assert VALID_PURPOSES == expected_purposes, (
            f"VALID_PURPOSES should be {expected_purposes}, got {VALID_PURPOSES}"
        )


class TestClassifyPurposeKeywordMatching:
    """Test keyword-based purpose classification (no LLM calls)."""

    def test_classify_purpose_diagram_keyword(self):
        """Classify prompt containing 'flowchart' keyword → should return 'diagram'."""
        client = LLMClient(
            api_key="test-key", model="test", base_url="http://localhost:1"
        )

        prompt = "Draw a flowchart of login process"
        result = client.classify_purpose(prompt)

        assert result == "diagram", (
            f"Expected 'diagram' for flowchart prompt, got '{result}'"
        )

    def test_classify_purpose_icon_keyword(self):
        """Classify prompt containing 'icon' keyword → should return 'icon'."""
        client = LLMClient(
            api_key="test-key", model="test", base_url="http://localhost:1"
        )

        prompt = "Create an icon for settings"
        result = client.classify_purpose(prompt)

        assert result == "icon", (
            f"Expected 'icon' for settings icon prompt, got '{result}'"
        )

    def test_classify_purpose_infographic_keyword(self):
        """Classify prompt containing 'infographic' keyword → should return 'infographic'."""
        client = LLMClient(
            api_key="test-key", model="test", base_url="http://localhost:1"
        )

        prompt = "Make an infographic about sales metrics and trends"
        result = client.classify_purpose(prompt)

        assert result == "infographic", (
            f"Expected 'infographic' for sales infographic prompt, got '{result}'"
        )

    def test_classify_purpose_flat_illustration_keyword(self):
        """Classify prompt containing 'flat' keyword → should return 'flat_illustration'."""
        client = LLMClient(
            api_key="test-key", model="test", base_url="http://localhost:1"
        )

        prompt = "Design a flat illustration of a team working together"
        result = client.classify_purpose(prompt)

        assert result == "flat_illustration", (
            f"Expected 'flat_illustration' for flat team design prompt, got '{result}'"
        )


class TestTemplateLoadingAndFallback:
    """Test template loading and fallback behavior."""

    def test_load_template_invalid_purpose_falls_back_to_classic(self):
        """Call load_template('nonexistent_purpose') and confirm fallback to classic."""
        # Load the nonexistent purpose (should fall back to classic)
        result = load_template("nonexistent_purpose")

        # Load classic directly for comparison
        classic = load_template("classic")

        # Should be identical
        assert result == classic, (
            "load_template('nonexistent_purpose') did not fall back to classic.yaml"
        )

    def test_load_template_returns_dict_with_system_prompt(self):
        """Verify load_template returns a dict with 'system_prompt' key."""
        template = load_template("classic")

        assert isinstance(template, dict), "load_template should return a dict"
        assert "system_prompt" in template, (
            "Loaded template should contain 'system_prompt' key"
        )

    def test_load_all_templates_returns_all_purposes(self):
        """Verify load_all_templates returns dict with all valid purposes."""
        all_templates = load_all_templates()

        assert isinstance(all_templates, dict), (
            "load_all_templates should return a dict"
        )

        # Should have all VALID_PURPOSES as keys (except component, which is not in VALID_PURPOSES)
        for purpose in VALID_PURPOSES:
            assert purpose in all_templates, (
                f"load_all_templates missing '{purpose}' key"
            )
            assert isinstance(all_templates[purpose], dict), (
                f"Template for '{purpose}' should be a dict"
            )


class TestModeValidation:
    """Test that mode validation constants are used correctly."""

    def test_mode_validation_in_generate_diagram_data(self):
        """Verify VALID_MODES is a list with 3 items for branching."""
        assert isinstance(VALID_MODES, list), "VALID_MODES should be a list"
        assert len(VALID_MODES) == 3, (
            f"VALID_MODES should have 3 items, got {len(VALID_MODES)}"
        )

        # Verify it contains the expected strings
        assert "direct_svg" in VALID_MODES
        assert "code_generation" in VALID_MODES
        assert "component" in VALID_MODES


class TestModuleImports:
    """Test that all core modules import cleanly."""

    def test_all_modules_import_cleanly(self):
        """Import llm_client, code_executor, composition_engine, svg_processor."""
        # These should all import without errors
        import llm_client
        import code_executor
        import composition_engine
        import svg_processor

        # Verify they're modules (have __name__ attribute)
        assert hasattr(llm_client, "__name__")
        assert hasattr(code_executor, "__name__")
        assert hasattr(composition_engine, "__name__")
        assert hasattr(svg_processor, "__name__")

    def test_code_executor_exports_required_symbols(self):
        """Verify code_executor exports expected constants and classes."""
        from code_executor import (
            CodeExecutor,
            CodeExecutionError,
            ImportViolationError,
            ALLOWED_IMPORTS,
            DANGEROUS_BUILTINS,
            SAFE_ENV_KEYS,
        )

        # Check they exist and are the correct type
        assert callable(CodeExecutor), "CodeExecutor should be callable (class)"
        assert issubclass(CodeExecutionError, Exception)
        assert issubclass(ImportViolationError, Exception)
        assert isinstance(ALLOWED_IMPORTS, set)
        assert isinstance(DANGEROUS_BUILTINS, set)
        assert isinstance(SAFE_ENV_KEYS, set)

    def test_llm_client_exports_required_symbols(self):
        """Verify llm_client exports required constants and functions."""
        from llm_client import (
            VALID_MODES,
            VALID_PURPOSES,
            load_template,
            load_all_templates,
            LLMClient,
        )

        assert isinstance(VALID_MODES, list)
        assert isinstance(VALID_PURPOSES, list)
        assert callable(load_template)
        assert callable(load_all_templates)
        assert callable(LLMClient)
