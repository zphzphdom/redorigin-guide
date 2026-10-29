# -*- coding: utf-8 -*-
"""运行配置：环境变量优先，其次 data/config.json，最后默认值。

支持两种来源（便于评审/部署）：
1) 环境变量：DEEPSEEK_API_KEY、DEEPSEEK_MODEL、DEEPSEEK_BASE_URL、REDORIGIN_LLM、REDORIGIN_SEARCH
2) 本地文件：data/config.json（可直接改，改完重启服务生效；不要提交到公开仓库）
"""
from __future__ import annotations

import json
import os
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
VERSION = "v1.3"


class Config:
    def __init__(self) -> None:
        file_cfg = {}
        f = DATA / "config.json"
        if f.exists():
            try:
                file_cfg = json.loads(f.read_text(encoding="utf-8-sig"))
            except Exception:
                file_cfg = {}

        self.api_key: str = (os.environ.get("DEEPSEEK_API_KEY") or file_cfg.get("api_key") or "").strip()
        self.base_url: str = (os.environ.get("DEEPSEEK_BASE_URL") or file_cfg.get("base_url")
                              or "https://api.deepseek.com").rstrip("/")
        self.model: str = os.environ.get("DEEPSEEK_MODEL") or file_cfg.get("model") or "deepseek-flash"
        self.timeout: float = float(os.environ.get("DEEPSEEK_TIMEOUT") or file_cfg.get("timeout") or 25)
        # 开关：有 key 才生效；显式设 0 可强制关闭（用于离线评审）
        self.llm_enabled: bool = bool(self.api_key) and os.environ.get("REDORIGIN_LLM", "1") != "0"
        self.search_enabled: bool = bool(self.api_key) and os.environ.get("REDORIGIN_SEARCH", "1") != "0"
        self.max_web_results: int = int(os.environ.get("REDORIGIN_WEB_RESULTS") or file_cfg.get("max_web_results") or 4)

    @property
    def mode(self) -> str:
        if self.llm_enabled:
            return "deepseek-api"
        return "offline-rules"

    def public_dict(self) -> dict:
        """给前端的能力声明，不泄露 key。"""
        return {
            "version": VERSION,
            "mode": self.mode,
            "model": self.model if self.llm_enabled else "本地规则引擎（BM25 + 模板）",
            "llm": self.llm_enabled,
            "search": self.search_enabled,
            "provider": "DeepSeek API" if self.api_key else "无（纯本地）",
            "web_results": self.max_web_results,
        }
