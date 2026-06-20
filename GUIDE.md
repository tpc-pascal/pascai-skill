## Hướng dẫn sử dụng

### Yêu cầu

- Python 3.11+
- Git

### Cài đặt

```bash
git clone https://github.com/tpc-pascal/pascai-skill.git
cd pascai-skill
pip install -e ".[dev]"
```

### Khởi tạo

```bash
pascai init
```

### Quản lý Skills

```bash
pascai skill list
pascai skill show <skill_id>
pascai skill enable <skill_id>
pascai skill disable <skill_id>
pascai skill search <query>
pascai skill install <url> [--branch main]
pascai skill sync <skill_id>
```

### Cập nhật

```bash
pascai update check <skill_id>
pascai update apply <skill_id>
pascai update rollback <skill_id> --version <hash>
pascai update history <skill_id>
```

### Memory & Knowledge

```bash
pascai memory set <key> <value> --namespace <ns>
pascai memory get <key> --namespace <ns>
pascai memory search <query>
pascai knowledge add <source> <content>
pascai knowledge search <query>
```

### Cấu trúc một Skill

```
skills/<skill_id>/
├── skill.yaml       # Metadata + upstream
├── prompts/         # Prompt templates (.md)
├── templates/       # Jinja2 templates (.jinja)
├── tools/           # Tool definitions (.yaml)
└── examples/        # Example scripts (.py)
```
