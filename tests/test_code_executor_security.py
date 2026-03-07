"""
Comprehensive security tests for code_executor.py sandbox.

Tests import validation, dangerous builtin blocking, environment variables,
and integration with the CodeExecutor.execute() method.
"""

import pytest
from code_executor import (
    CodeExecutor,
    CodeExecutionError,
    ImportViolationError,
    ALLOWED_IMPORTS,
    DANGEROUS_BUILTINS,
    SAFE_ENV_KEYS,
    TIMEOUT_SECONDS,
)


# ============================================================================
# IMPORT WHITELIST TESTS
# ============================================================================


class TestImportWhitelist:
    """Test that validate_imports() correctly enforces the import whitelist."""

    def test_allowed_imports_pass(self):
        """Test that all allowed imports pass validation."""
        code = "import drawsvg\nimport math\nimport colorsys\nimport random"
        violations = CodeExecutor.validate_imports(code)
        assert violations == []

    def test_disallowed_import_os_blocked(self):
        """Test that importing 'os' is blocked."""
        code = "import os"
        violations = CodeExecutor.validate_imports(code)
        assert "os" in violations

    def test_disallowed_import_subprocess_blocked(self):
        """Test that importing 'subprocess' is blocked."""
        code = "import subprocess"
        violations = CodeExecutor.validate_imports(code)
        assert "subprocess" in violations

    def test_disallowed_import_sys_blocked(self):
        """Test that importing 'sys' is blocked."""
        code = "import sys"
        violations = CodeExecutor.validate_imports(code)
        assert "sys" in violations

    def test_disallowed_from_import_blocked(self):
        """Test that 'from os import path' is blocked."""
        code = "from os import path"
        violations = CodeExecutor.validate_imports(code)
        assert "os" in violations

    def test_disallowed_import_socket_blocked(self):
        """Test that importing 'socket' is blocked."""
        code = "import socket"
        violations = CodeExecutor.validate_imports(code)
        assert "socket" in violations


# ============================================================================
# DANGEROUS BUILTINS TESTS
# ============================================================================


class TestDangerousBuiltins:
    """Test that validate_builtins() correctly blocks dangerous functions."""

    def test_dangerous_exec_blocked(self):
        """Test that exec() is detected and blocked."""
        code = "exec('import os')"
        violations = CodeExecutor.validate_builtins(code)
        assert "exec" in violations

    def test_dangerous_eval_blocked(self):
        """Test that eval() is detected and blocked."""
        code = "result = eval('1+1')"
        violations = CodeExecutor.validate_builtins(code)
        assert "eval" in violations

    def test_dangerous_open_blocked(self):
        """Test that open() is detected and blocked."""
        code = "f = open('/etc/passwd')"
        violations = CodeExecutor.validate_builtins(code)
        assert "open" in violations

    def test_dangerous_dunder_import_blocked(self):
        """Test that __import__() is detected and blocked."""
        code = "__import__('os')"
        violations = CodeExecutor.validate_builtins(code)
        assert "__import__" in violations

    def test_dangerous_compile_blocked(self):
        """Test that compile() is detected and blocked."""
        code = "compile('code', '', 'exec')"
        violations = CodeExecutor.validate_builtins(code)
        assert "compile" in violations

    def test_safe_code_passes_builtins_check(self):
        """Test that safe code with no dangerous builtins passes validation."""
        code = "import math\nx = math.sin(3.14)\nprint(x)"
        violations = CodeExecutor.validate_builtins(code)
        assert violations == []


# ============================================================================
# EXECUTE INTEGRATION TESTS
# ============================================================================


class TestExecuteIntegration:
    """Test that CodeExecutor.execute() correctly blocks violations."""

    def test_execute_blocks_disallowed_import(self):
        """Test that execute() blocks code attempting to import 'os'."""
        code = "import os\nprint(os.getcwd())"
        with pytest.raises(ImportViolationError):
            CodeExecutor.execute(code)

    def test_execute_blocks_dangerous_builtin(self):
        """Test that execute() blocks code attempting to use exec()."""
        code = "exec('print(1)')"
        with pytest.raises(ImportViolationError):
            CodeExecutor.execute(code)

    def test_execute_blocks_syntax_error(self):
        """Test that execute() raises CodeExecutionError for syntax errors."""
        code = "def f(\n"
        with pytest.raises(CodeExecutionError):
            CodeExecutor.execute(code)


# ============================================================================
# ENVIRONMENT VARIABLE WHITELIST TESTS
# ============================================================================


class TestSafeEnvKeys:
    """Test that SAFE_ENV_KEYS correctly excludes API keys and secrets."""

    def test_safe_env_keys_does_not_include_api_key(self):
        """Test that API_KEY and OPENAI_API_KEY are NOT in SAFE_ENV_KEYS."""
        assert "OPENAI_API_KEY" not in SAFE_ENV_KEYS
        assert "API_KEY" not in SAFE_ENV_KEYS

    def test_safe_env_keys_includes_path(self):
        """Test that PATH is included in SAFE_ENV_KEYS."""
        assert "PATH" in SAFE_ENV_KEYS


# ============================================================================
# TIMEOUT TEST
# ============================================================================


class TestTimeout:
    """Test that CodeExecutor properly enforces timeouts."""

    @pytest.mark.slow
    def test_execute_timeout_on_infinite_loop(self):
        """Test that execute() raises CodeExecutionError on infinite loop timeout."""
        code = "while True: pass"
        with pytest.raises(CodeExecutionError) as exc_info:
            CodeExecutor.execute(code)
        assert "timed out" in str(exc_info.value.message).lower()


# ============================================================================
# CONSTANTS TESTS
# ============================================================================


class TestConstants:
    """Test the security constants themselves."""

    def test_allowed_imports_is_minimal(self):
        """Test that ALLOWED_IMPORTS contains exactly the expected modules."""
        assert ALLOWED_IMPORTS == {"drawsvg", "math", "colorsys", "random"}

    def test_dangerous_builtins_includes_critical(self):
        """Test that DANGEROUS_BUILTINS includes all critical dangerous names."""
        critical = {"exec", "eval", "compile", "__import__", "open"}
        assert critical.issubset(DANGEROUS_BUILTINS)

    def test_timeout_seconds_is_positive(self):
        """Test that TIMEOUT_SECONDS is set to a positive value."""
        assert TIMEOUT_SECONDS > 0
        assert TIMEOUT_SECONDS == 10
