# pascai-skill
Hệ điều hành AI di động — Portable AI Operating System cho đa tác tử (multi-agent)

<p align="center">
  <img src="assets/logo.svg" alt="pascai-skill logo" width="400">
</p>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![OpenCode](https://img.shields.io/badge/OpenCode-ready-blueviolet)](https://opencode.ai)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ready-black)](https://docs.anthropic.com/en/docs/claude-code/overview)
[![Cursor](https://img.shields.io/badge/Cursor-ready-6c47ff)](https://cursor.com)
[![Aider](https://img.shields.io/badge/Aider-ready-3b82f6)](https://aider.chat)
[![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-ready-4285f4)](https://cloud.google.com/vertex-ai/generative-ai/docs/overview)
[![Codex](https://img.shields.io/badge/Codex-ready-10a37f)](https://github.com/features/copilot)

> Hệ thống dạng plugin, hoạt động như một AI Operating System: tự động phát hiện skills, quản lý upstream, đồng bộ phiên bản, và tương thích với mọi tác tử AI.

---

## Tính năng

- Plugin Architecture — Skills tự động phát hiện, không hardcode
- 6 Adapters — OpenCode, Claude Code, Cursor, Aider, Gemini CLI, Codex
- Upstream Management — Clone, sync, changelog, rollback từ GitHub
- Update Engine — Kiểm tra cập nhật, backup, migration, rollback
- Long-term Memory — SQLite store
- Knowledge Base — Filesystem store
- CLI đầy đủ — 20+ commands

---

## Skills tích hợp sẵn

| Skill | Upstream | Chức năng |
|---|---|---|
| Document Intelligence | [Docling](https://github.com/docling-project/docling) | PDF, DOCX, PPTX, XLSX, images → Markdown |
| Long Term Memory | [Ponytail](https://github.com/DietrichGebert/ponytail) | Lưu architecture, conventions, todos, bugs |
| Context Compression | [Headroom](https://github.com/chopratejas/headroom) | Nén logs, JSON, tool responses, RAG |
| UI & Design Intelligence | [Taste Skill](https://github.com/Leonxlnx/taste-skill) | Typography, spacing, 4 design profiles |
| Documentation Generator | [Docusaurus](https://github.com/facebook/docusaurus) | Tạo site tài liệu từ skills |

---

## Quick Start

```bash
git clone https://github.com/tpc-pascal/pascai-skill.git
cd pascai-skill
pip install -e ".[dev]"
pascai init
pascai status
pascai skill list
```

---

## Tech Stack

| Layer | Công nghệ |
|---|---|
| Language | Python 3.11+ |
| Validation | Pydantic 2.x |
| CLI | Click + Rich |
| Git | GitPython |
| Memory | SQLite |
| Knowledge | Filesystem (JSON) |

---

## Tác giả

**tpc-pascal** — [GitHub](https://github.com/tpc-pascal)

---

## License

MIT
