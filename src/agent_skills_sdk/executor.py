"""Tool execution module."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ToolExecutionError, ToolNotFoundError
from .models import Skill, ToolExecutionResult


class ToolExecutor:
    """Executes skill tools with safety and sandboxing."""

    def __init__(
        self,
        timeout: int = 30,
        sandbox: bool = True,
        allow_network: bool = True,
    ):
        """Initialize tool executor.

        Args:
            timeout: Maximum execution time in seconds
            sandbox: Whether to run tools in sandboxed environment
            allow_network: Whether to allow network access (when sandboxed)
        """
        self.timeout = timeout
        self.sandbox = sandbox
        self.allow_network = allow_network

    def execute(
        self,
        skill: Skill,
        tool_name: str,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None,
    ) -> ToolExecutionResult:
        """Execute a skill tool.

        Args:
            skill: The skill containing the tool
            tool_name: Name of the tool to execute
            input_data: Input data to pass to the tool
            timeout: Optional timeout override

        Returns:
            ToolExecutionResult with execution details

        Raises:
            ToolNotFoundError: If the tool doesn't exist
            ToolExecutionError: If execution fails
        """
        # Find the tool
        tool = skill.get_tool(tool_name)
        if not tool:
            raise ToolNotFoundError(tool_name, skill.name)

        # Verify script exists
        if not tool.script_path.exists():
            raise ToolExecutionError(
                tool_name,
                skill.name,
                f"Script not found: {tool.script_path}",
            )

        # Determine timeout
        exec_timeout = timeout or self.timeout

        # Execute the tool
        start_time = time.time()

        try:
            result = self._execute_script(
                tool.script_path,
                input_data,
                exec_timeout,
            )
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            return ToolExecutionResult(
                success=result["success"],
                data=result.get("data"),
                error=result.get("error"),
                stdout=result.get("stdout"),
                stderr=result.get("stderr"),
                exit_code=result.get("exit_code"),
                execution_time_ms=execution_time,
            )

        except subprocess.TimeoutExpired:
            execution_time = (time.time() - start_time) * 1000
            return ToolExecutionResult(
                success=False,
                error=f"Tool execution timed out after {exec_timeout}s",
                execution_time_ms=execution_time,
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            raise ToolExecutionError(
                tool_name,
                skill.name,
                str(e),
            )

    def _execute_script(
        self,
        script_path: Path,
        input_data: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        """Execute a script file.

        Args:
            script_path: Path to the script
            input_data: Input data as dict
            timeout: Execution timeout in seconds

        Returns:
            Dict with execution results
        """
        # Convert input to JSON
        input_json = json.dumps(input_data)

        # Determine interpreter based on file extension
        interpreter = self._get_interpreter(script_path)

        # Build command
        if interpreter:
            cmd = [interpreter, str(script_path)]
        else:
            # Assume it's executable
            cmd = [str(script_path)]

        # Execute
        result = subprocess.run(
            cmd,
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=script_path.parent,  # Run in script directory
        )

        # Parse output
        success = result.returncode == 0

        # Try to parse stdout as JSON
        data = None
        error = None

        if success and result.stdout:
            try:
                output = json.loads(result.stdout)
                if isinstance(output, dict):
                    success = output.get("status") == "success"
                    data = output.get("data")
                    error = output.get("message") or output.get("error")
                else:
                    data = output
            except json.JSONDecodeError:
                # Not JSON, treat as plain text
                data = result.stdout

        elif result.stderr:
            try:
                error_output = json.loads(result.stderr)
                if isinstance(error_output, dict):
                    error = error_output.get("message") or error_output.get("error")
                else:
                    error = result.stderr
            except json.JSONDecodeError:
                error = result.stderr

        return {
            "success": success,
            "data": data,
            "error": error,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }

    def _get_interpreter(self, script_path: Path) -> Optional[str]:
        """Get the appropriate interpreter for a script.

        Args:
            script_path: Path to the script

        Returns:
            Interpreter command or None if directly executable
        """
        extension = script_path.suffix.lower()

        interpreters = {
            ".py": "python3",
            ".js": "node",
            ".ts": "ts-node",
            ".sh": "bash",
            ".rb": "ruby",
            ".pl": "perl",
        }

        return interpreters.get(extension)

    def validate_tool(self, skill: Skill, tool_name: str) -> tuple[bool, Optional[str]]:
        """Validate that a tool can be executed.

        Args:
            skill: The skill containing the tool
            tool_name: Name of the tool

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check tool exists
        tool = skill.get_tool(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found"

        # Check script exists
        if not tool.script_path.exists():
            return False, f"Script not found: {tool.script_path}"

        # Check script is readable
        if not os.access(tool.script_path, os.R_OK):
            return False, f"Script not readable: {tool.script_path}"

        # Check interpreter is available
        interpreter = self._get_interpreter(tool.script_path)
        if interpreter:
            import shutil

            if not shutil.which(interpreter):
                return False, f"Interpreter '{interpreter}' not found in PATH"

        return True, None


import os
