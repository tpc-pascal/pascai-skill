import pytest
from pascai_skill.adapters.opencode import OpenCodeAdapter
from pascai_skill.adapters.claude_code import ClaudeCodeAdapter
from pascai_skill.adapters.cursor import CursorAdapter
from pascai_skill.adapters.aider import AiderAdapter
from pascai_skill.adapters.gemini_cli import GeminiCliAdapter
from pascai_skill.adapters.codex import CodexAdapter


class TestAdapters:
    def test_opencode_adapter(self):
        adapter = OpenCodeAdapter()
        assert adapter.name == "opencode"
        config = adapter.generate_config()
        assert "opencode_specific" in config

    def test_claude_code_adapter(self):
        adapter = ClaudeCodeAdapter()
        assert adapter.name == "claude_code"
        config = adapter.generate_config()
        assert "claude_code_specific" in config
        assert config["claude_code_specific"]["prompt_caching"]

    def test_cursor_adapter(self):
        adapter = CursorAdapter()
        assert adapter.name == "cursor"
        config = adapter.generate_config()
        assert "cursor_specific" in config

    def test_aider_adapter(self):
        adapter = AiderAdapter()
        assert adapter.name == "aider"
        config = adapter.generate_config()
        assert "aider_specific" in config

    def test_gemini_cli_adapter(self):
        adapter = GeminiCliAdapter()
        assert adapter.name == "gemini_cli"
        config = adapter.generate_config()
        assert "gemini_cli_specific" in config

    def test_codex_adapter(self):
        adapter = CodexAdapter()
        assert adapter.name == "codex"
        config = adapter.generate_config()
        assert "codex_specific" in config

    def test_all_adapters_have_unique_names(self):
        names = [OpenCodeAdapter().name, ClaudeCodeAdapter().name, CursorAdapter().name,
                 AiderAdapter().name, GeminiCliAdapter().name, CodexAdapter().name]
        assert len(names) == len(set(names))
