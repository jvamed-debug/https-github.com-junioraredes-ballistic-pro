"""Tests for Release 0.8 — CLI (config, interactive mode)."""

from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cli.config import ConfigManager, PlatformConfig
from cli.interactive import InteractiveShell


class TestConfigManager(unittest.TestCase):
    def test_default_config(self) -> None:
        mgr = ConfigManager(base_dir="/tmp/nonexistent")
        cfg = mgr.load()
        assert cfg.language == "python"
        assert cfg.default_provider == "openai"

    def test_set_and_get(self) -> None:
        mgr = ConfigManager(base_dir="/tmp/nonexistent")
        mgr.load()
        assert mgr.set("language", "go") is True
        assert mgr.get("language") == "go"

    def test_set_unknown_key(self) -> None:
        mgr = ConfigManager(base_dir="/tmp/nonexistent")
        mgr.load()
        assert mgr.set("nonexistent_key", "value") is False

    def test_set_provider(self) -> None:
        mgr = ConfigManager(base_dir="/tmp/nonexistent")
        mgr.load()
        mgr.set_provider("anthropic", api_key="sk-test", base_url="https://api.anthropic.com")
        provider = mgr.get_provider("anthropic")
        assert provider["api_key"] == "sk-test"

    def test_reset(self) -> None:
        mgr = ConfigManager(base_dir="/tmp/nonexistent")
        mgr.load()
        mgr.set("language", "rust")
        mgr.reset()
        assert mgr.config.language == "python"


class TestInteractiveShell(unittest.TestCase):
    def test_help_command(self) -> None:
        shell = InteractiveShell()
        result = shell.execute("help")
        assert result.success is True
        assert "Available commands" in result.output

    def test_unknown_command(self) -> None:
        shell = InteractiveShell()
        result = shell.execute("foobar")
        assert result.success is False
        assert "Unknown command" in result.output

    def test_history(self) -> None:
        shell = InteractiveShell()
        shell.execute("help")
        shell.execute("status")
        result = shell.execute("history")
        assert "help" in result.output
        assert "status" in result.output
        assert len(shell.history) == 3

    def test_config_set_get(self) -> None:
        shell = InteractiveShell()
        result = shell.execute("config language=python")
        assert "Set language = python" in result.output
        result = shell.execute("config language")
        assert "python" in result.output

    def test_agents_command(self) -> None:
        shell = InteractiveShell()
        result = shell.execute("agents")
        assert "orchestrator" in result.output
        assert "developer" in result.output

    def test_status_command(self) -> None:
        shell = InteractiveShell()
        result = shell.execute("status")
        assert "EAP Status" in result.output

    def test_exit_command(self) -> None:
        shell = InteractiveShell()
        result = shell.execute("exit")
        assert "Goodbye" in result.output

    def test_empty_command(self) -> None:
        shell = InteractiveShell()
        result = shell.execute("")
        assert result.success is True

    def test_clear_history(self) -> None:
        shell = InteractiveShell()
        shell.execute("help")
        shell.execute("clear")
        assert len(shell.history) == 0

    def test_available_commands(self) -> None:
        shell = InteractiveShell()
        cmds = shell.available_commands
        assert "help" in cmds
        assert "exit" in cmds
        assert "agents" in cmds

    def test_set_context(self) -> None:
        shell = InteractiveShell()
        shell.set_context("project", "MyApp")
        result = shell.execute("status")
        assert "MyApp" in result.output

    def test_register_custom_command(self) -> None:
        shell = InteractiveShell()
        shell.register_command("greet", lambda args: __import__(
            "cli.interactive", fromlist=["CommandResult"]
        ).CommandResult(output=f"Hello {args}"))
        result = shell.execute("greet World")
        assert result.output == "Hello World"


if __name__ == "__main__":
    unittest.main()
