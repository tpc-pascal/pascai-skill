# Hướng dẫn Đóng góp (Contributing Guidelines)

Vui lòng đọc kỹ các hướng dẫn dưới đây trước khi bắt đầu đóng góp.

---

## 🛠 1. Thiết lập môi trường phát triển (Setup)

```bash
git clone https://github.com/tpc-pascal/pascai-skill.git
cd pascai-skill
pip install -e ".[dev]"
pascai init
pascai status
```

---

## 🌿 2. Quy trình gửi đóng góp (Git Workflow)

1. **Fork** dự án về tài khoản cá nhân.
2. **Tạo Branch mới:**
   - Tính năng mới: `git checkout -b feat/ten-tinh-nang`
   - Sửa lỗi: `git checkout -b fix/ten-loi`
   - Tài liệu: `git checkout -b docs/ten-tai-lieu`
3. **Commit:** rõ nghĩa, có prefix.
4. **Push & PR:** Tạo Pull Request.

---

## 📝 3. Quy chuẩn viết mã

- Python 3.11+, type hints
- Pydantic cho data models
- SOLID principles
- Test cho mọi logic mới
- `snake_case` cho functions/variables, `PascalCase` cho classes

---

## 🧪 4. Kiểm thử

```bash
pytest tests/ -v
```

---

## 📧 Liên hệ

- [Mở Issue](https://github.com/tpc-pascal/pascai-skill/issues)
