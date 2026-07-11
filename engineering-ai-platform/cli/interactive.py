"""CLI Interactive Mode — modo interativo REPL para a plataforma."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandResult:
    output: str
    success: bool = True
    data: Any = None


class InteractiveShell:
    """Shell interativo com comandos built-in e histórico."""

    def __init__(self) -> None:
        self._history: list[str] = []
        self._commands: dict[str, Any] = {}
        self._running = False
        self._context: dict[str, Any] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self._commands["help"] = self._cmd_help
        self._commands["history"] = self._cmd_history
        self._commands["clear"] = self._cmd_clear
        self._commands["status"] = self._cmd_status
        self._commands["agents"] = self._cmd_agents
        self._commands["config"] = self._cmd_config
        self._commands["exit"] = self._cmd_exit
        self._commands["quit"] = self._cmd_exit

    def register_command(self, name: str, handler: Any) -> None:
        self._commands[name] = handler

    def execute(self, command_line: str) -> CommandResult:
        command_line = command_line.strip()
        if not command_line:
            return CommandResult(output="", success=True)

        self._history.append(command_line)
        parts = command_line.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        handler = self._commands.get(cmd)
        if handler is None:
            return CommandResult(
                output=f"Unknown command: '{cmd}'. Type 'help' for available commands.",
                success=False,
            )

        return handler(args)

    def _cmd_help(self, args: str = "") -> CommandResult:
        lines = ["Available commands:"]
        for name in sorted(self._commands.keys()):
            lines.append(f"  {name}")
        return CommandResult(output="\n".join(lines))

    def _cmd_history(self, args: str = "") -> CommandResult:
        if not self._history:
            return CommandResult(output="No command history.")
        lines = [f"  {i+1}. {cmd}" for i, cmd in enumerate(self._history)]
        return CommandResult(output="\n".join(lines))

    def _cmd_clear(self, args: str = "") -> CommandResult:
        self._history.clear()
        return CommandResult(output="History cleared.")

    def _cmd_status(self, args: str = "") -> CommandResult:
        project = self._context.get("project", "Not initialized")
        return CommandResult(
            output=f"EAP Status\n  Project: {project}\n  Version: 1.0.0\n  Mode: Interactive",
            data={"project": project, "version": "1.0.0"},
        )

    def _cmd_agents(self, args: str = "") -> CommandResult:
        agents = [
            "orchestrator", "architect", "developer", "reviewer",
            "security", "planner", "knowledge", "documentation",
        ]
        lines = ["Registered agents:"]
        for a in agents:
            lines.append(f"  - {a}")
        return CommandResult(output="\n".join(lines))

    def _cmd_config(self, args: str = "") -> CommandResult:
        if not args:
            items = [f"  {k}: {v}" for k, v in self._context.items()]
            return CommandResult(output="Current config:\n" + "\n".join(items) if items else "No config set.")

        parts = args.split("=", maxsplit=1)
        if len(parts) == 2:
            key, value = parts[0].strip(), parts[1].strip()
            self._context[key] = value
            return CommandResult(output=f"Set {key} = {value}")
        return CommandResult(output=f"Config value: {self._context.get(args.strip(), 'not set')}")

    def _cmd_exit(self, args: str = "") -> CommandResult:
        self._running = False
        return CommandResult(output="Goodbye!")

    def set_context(self, key: str, value: Any) -> None:
        self._context[key] = value

    @property
    def history(self) -> list[str]:
        return list(self._history)

    @property
    def available_commands(self) -> list[str]:
        return sorted(self._commands.keys())

    @property
    def is_running(self) -> bool:
        return self._running
