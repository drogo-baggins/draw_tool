"""
Executes LLM-generated Python code in a sandboxed subprocess to produce SVG output.

This module provides safe execution of dynamically generated Python code with:
- Import validation using AST analysis against a whitelist
- Subprocess isolation with timeout protection
- SVG output capture and validation
- Clear error reporting for debugging
"""

import ast
import os
import re
import subprocess
import sys
import tempfile
from typing import List


ALLOWED_IMPORTS = {"drawsvg", "math", "colorsys", "random"}
TIMEOUT_SECONDS = 10

# Built-in functions that can bypass import restrictions or cause harm
DANGEROUS_BUILTINS = {
    "exec", "eval", "compile", "__import__", "open",
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr",
    "breakpoint", "input", "memoryview",
    "__loader__", "__spec__", "__builtins__",
}

# Environment variables passed to the subprocess (allowlist)
SAFE_ENV_KEYS = {
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE",
    "TEMP", "TMP", "USERPROFILE", "HOME",
    "HOMEDRIVE", "HOMEPATH",
    "PYTHONDONTWRITEBYTECODE",
}


class CodeExecutionError(Exception):
    """Raised when code execution fails for any reason."""

    def __init__(self, message: str, stderr: str = "", stdout: str = ""):
        """Initialize error with message and optional stderr/stdout capture."""
        self.message = message
        self.stderr = stderr
        self.stdout = stdout
        super().__init__(self.message)


class ImportViolationError(CodeExecutionError):
    """Raised when code imports modules not in the allowed list."""

    pass


class CodeExecutor:
    """Safely executes LLM-generated Python code with sandboxing and validation."""

    @staticmethod
    def validate_imports(code: str) -> List[str]:
        """
        Validate that all imports in the code are in ALLOWED_IMPORTS.

        Args:
            code: Python code to validate

        Returns:
            List of violated module names (empty list if valid)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise CodeExecutionError(f"Failed to parse generated code: {e}")

        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name not in ALLOWED_IMPORTS:
                        violations.append(module_name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if module_name not in ALLOWED_IMPORTS:
                        violations.append(module_name)

        return violations

    @staticmethod
    def validate_builtins(code: str) -> List[str]:
        """
        Validate that the code does not call dangerous built-in functions
        that could bypass import restrictions (e.g. exec, eval, __import__).

        Args:
            code: Python code to validate (must already be parseable)

        Returns:
            List of dangerous call names found (empty list if clean)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # SyntaxError will already be caught in validate_imports
            return []

        found: List[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Direct call: exec(...), eval(...), __import__(...)
                if isinstance(node.func, ast.Name):
                    if node.func.id in DANGEROUS_BUILTINS:
                        found.append(node.func.id)
                # Attribute call: builtins.exec(...), obj.__class__.__init__(...)
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in DANGEROUS_BUILTINS:
                        found.append(node.func.attr)
            # Detect attribute access even without a call (e.g. g = globals)
            elif isinstance(node, ast.Attribute):
                if node.attr in DANGEROUS_BUILTINS:
                    found.append(node.attr)
            elif isinstance(node, ast.Name):
                if node.id in DANGEROUS_BUILTINS:
                    found.append(node.id)

        return found

    @staticmethod
    def execute(code: str) -> str:
        """
        Execute code in a subprocess and capture SVG output.

        Args:
            code: Python code to execute

        Returns:
            SVG string from code execution

        Raises:
            ImportViolationError: If code imports disallowed modules
            CodeExecutionError: If execution fails, times out, or doesn't produce SVG
        """
        # Validate imports
        violations = CodeExecutor.validate_imports(code)
        if violations:
            raise ImportViolationError(
                f"Code imports disallowed modules: {', '.join(set(violations))}"
            )

        # Validate dangerous built-in usage
        dangerous = CodeExecutor.validate_builtins(code)
        if dangerous:
            raise ImportViolationError(
                f"Code uses dangerous built-ins: {', '.join(set(dangerous))}"
            )

        # Create temporary directory and file for execution
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, "exec_code.py")

            with open(tmpfile, "w") as f:
                f.write(code)

            # Prepare environment: pass only whitelisted keys to prevent
            # leaking secrets (e.g. OPENAI_API_KEY) into the subprocess.
            env = {k: v for k, v in os.environ.items() if k in SAFE_ENV_KEYS}
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            # Execute code in subprocess with timeout
            try:
                result = subprocess.run(
                    [sys.executable, tmpfile],
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SECONDS,
                    cwd=tmpdir,
                    env=env,
                )
            except subprocess.TimeoutExpired as e:
                raise CodeExecutionError(
                    f"Code execution timed out after {TIMEOUT_SECONDS} seconds",
                    stderr=e.stderr or "",
                    stdout=e.stdout or "",
                )

            # Check for execution errors
            if result.returncode != 0:
                raise CodeExecutionError(
                    f"Code execution failed with return code {result.returncode}",
                    stderr=result.stderr,
                    stdout=result.stdout,
                )

            # Extract and validate SVG output
            stdout = result.stdout
            svg_match = re.search(r"<svg.*?</svg>", stdout, re.DOTALL | re.IGNORECASE)

            if not svg_match:
                raise CodeExecutionError(
                    "Code did not produce valid SVG output",
                    stderr=result.stderr,
                    stdout=result.stdout,
                )

            return svg_match.group(0)
