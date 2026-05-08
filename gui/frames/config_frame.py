"""
Config page: visual editor for .env file, grouped by category.
"""

import os
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from dotenv import set_key

from core.config import ConfigurationManager


_ENV_PATH = Path(__file__).parent.parent.parent / ".env"

# (env_key, label, sensitive, placeholder)
_AI_CORE_FIELDS = [
    ("AICORE_AUTH_URL",       "Auth URL",         False, "https://..."),
    ("AICORE_CLIENT_ID",      "Client ID",        False, "sb-..."),
    ("AICORE_CLIENT_SECRET",  "Client Secret",    True,  ""),
    ("AICORE_BASE_URL",       "Base URL",         False, "https://api.ai..."),
    ("AICORE_RESOURCE_GROUP", "Resource Group",   False, "default"),
]
_HANA_FIELDS = [
    ("HANA_ADDRESS",      "Address",         False, "xxx.hanacloud.ondemand.com"),
    ("HANA_PORT",         "Port",            False, "443"),
    ("HANA_USER",         "User",            False, ""),
    ("HANA_PASSWORD",     "Password",        True,  ""),
    ("HANA_SCHEMA",       "Schema",          False, ""),
    ("HANA_SCHEMA_CUST",  "Schema (Cust)",   False, ""),
]
_PROC_FIELDS = [
    ("AI_PROVIDER",       "AI Provider",         False, "claude"),
    ("LANGUAGE",          "Language",            False, "ja"),
    ("LLM_BATCH_SIZE",    "LLM Batch Size",      False, "30"),
    ("LLM_MAX_WORKERS",   "LLM Max Workers",     False, "5"),
    ("FILE_MAX_WORKERS",  "File Max Workers",    False, "5"),
    ("CUSTOM_FIELD_THRESHOLD", "CF Threshold",   False, "0.75"),
    ("UPLOAD_MODE",       "Upload Mode",         False, "overwrite"),
    ("Match_Number",      "Match Number",        False, "3"),
]
_VERIFY_FIELDS = [
    ("VERIFY_FLAG",     "Verify Flag",      False, "false"),
    ("ODATA_URL",       "OData URL",        False, "https://..."),
    ("ODATA_USER",      "OData User",       False, ""),
    ("ODATA_PASSWORD",  "OData Password",   True,  ""),
]
_MODEL_FIELDS = [
    ("CLAUDE_LLM_MODEL",   "Claude LLM Model",    False, "anthropic--claude-4.6-sonnet"),
    ("GEMINI_LLM_MODEL",   "Gemini LLM Model",    False, "gemini-2.5-pro"),
    ("OPENAI_LLM_MODEL",   "OpenAI LLM Model",    False, "gpt-4o"),
    ("TEXT_EMBEDDING_MODEL", "Embedding Model",   False, "text-embedding-ada-002"),
]


class ConfigFrame(ctk.CTkFrame):

    def __init__(self, parent, config_manager: ConfigurationManager):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.config_manager = config_manager
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Title + save button row
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        ctk.CTkLabel(hdr, text="配置",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(hdr, text="保存配置", width=110, height=32,
                      command=self._save).pack(side="right")
        self._save_label = ctk.CTkLabel(hdr, text="", text_color="gray")
        self._save_label.pack(side="right", padx=(0, 10))

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        groups = [
            ("SAP AI Core", _AI_CORE_FIELDS),
            ("HANA Cloud",  _HANA_FIELDS),
            ("处理参数",     _PROC_FIELDS),
            ("AI 模型",      _MODEL_FIELDS),
            ("OData 验证",   _VERIFY_FIELDS),
        ]

        row = 0
        col = 0
        for group_name, fields in groups:
            card = self._make_group_card(scroll, group_name, fields)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            col += 1
            if col > 1:
                col = 0
                row += 1

    def _make_group_card(self, parent, title: str, fields: list) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont(weight="bold", size=13)).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 4))

        for i, (key, label, sensitive, placeholder) in enumerate(fields, start=1):
            ctk.CTkLabel(card, text=label, anchor="w",
                         font=ctk.CTkFont(size=11)).grid(
                row=i, column=0, sticky="w", padx=(12, 6), pady=2)

            entry = ctk.CTkEntry(
                card,
                show="*" if sensitive else "",
                placeholder_text=placeholder,
                font=ctk.CTkFont(size=11),
            )
            entry.grid(row=i, column=1, sticky="ew", padx=(0, 12), pady=2)

            current = os.getenv(key, "")
            if current:
                entry.insert(0, current)

            self._entries[key] = entry

        # padding row
        ctk.CTkLabel(card, text="").grid(
            row=len(fields) + 1, column=0, pady=(0, 4))
        return card

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        if not _ENV_PATH.exists():
            messagebox.showerror("错误", f".env 文件不存在：{_ENV_PATH}")
            return

        changed = 0
        for key, entry in self._entries.items():
            val = entry.get()
            if val:
                set_key(str(_ENV_PATH), key, val)
                os.environ[key] = val
                changed += 1

        self._save_label.configure(
            text=f"已保存 {changed} 项 ✓", text_color="#81c784")
        self.after(3000, lambda: self._save_label.configure(text="", text_color="gray"))
