# -*- coding: utf-8 -*-
"""生成演示账号（PBKDF2-SHA256 加盐哈希）。运行：python tools/make_users.py"""
import hashlib, json, secrets, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
ACCOUNTS = [
    ("judge01", "HongYuan@2026", "评审专家体验账号", "judge"),
    ("judge02", "YanAn@2026", "评审专家体验账号", "judge"),
    ("demo", "demo2026", "公开演示账号", "demo"),
]


def main() -> None:
    users = []
    for username, pwd, display, role in ACCOUNTS:
        salt = secrets.token_bytes(16)
        it = 120_000
        h = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, it).hex()
        users.append({"username": username, "display": display, "role": role,
                      "salt": salt.hex(), "hash": h, "iterations": it})
    (DATA / "users.json").write_text(json.dumps({"users": users}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已写入 {DATA / 'users.json'}：")
    for u, p, _, _ in ACCOUNTS:
        print(f"  {u} / {p}")


if __name__ == "__main__":
    main()
