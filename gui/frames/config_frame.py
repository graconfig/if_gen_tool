"""
Config page: visual editor for .env file, grouped by category.
"""

import os
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from dotenv import set_key

from utils.i18n import _
from core.config import ConfigurationManager
from core.paths import get_base_path
from core.work_dir import get_work_dir, set_work_dir

# (env_key, label_msgid, sensitive, placeholder)
_AI_CORE_FIELDS = [
    ("AICORE_AUTH_URL",       "Auth URL",         False, "https://..."),
    ("AICORE_CLIENT_ID",      "Client ID",        False, "sb-..."),
    ("AICORE_CLIENT_SECRET",  "Client Secret",    True,  ""),
    ("AICORE_BASE_URL",       "Base URL",         False, "https://api.ai..."),
    ("AICORE_RESOURCE_GROUP", "Resource Group",   False, "default"),
]
_HANA_FIELDS = [
    ("HANA_ADDRESS",      "Address",       False, "xxx.hanacloud.ondemand.com"),
    ("HANA_PORT",         "Port",          False, "443"),
    ("HANA_USER",         "User",          False, ""),
    ("HANA_PASSWORD",     "Password",      True,  ""),
    ("HANA_SCHEMA",       "Schema",        False, ""),
    ("HANA_SCHEMA_CUST",  "Schema (Cust)", False, ""),
]
_PROC_FIELDS = [
    ("AI_PROVIDER",            "AI Provider",      False, "claude"),
    ("LANGUAGE",               "Language",         False, "ja"),
    ("LLM_BATCH_SIZE",         "LLM Batch Size",   False, "30"),
    ("LLM_MAX_WORKERS",        "LLM Max Workers",  False, "5"),
    ("FILE_MAX_WORKERS",       "File Max Workers", False, "5"),
    ("CUSTOM_FIELD_THRESHOLD", "CF Threshold",     False, "0.75"),
    ("MATCH_THRESHOLD",        "Match Threshold",  False, "0"),
    ("UPLOAD_MODE",            "Upload Mode",      False, "overwrite"),
    ("Match_Number",           "Match Number",     False, "3"),
]
_VERIFY_FIELDS = [
    ("VERIFY_FLAG",     "Verify Flag",    False, "false"),
    ("ODATA_URL",       "OData URL",      False, "https://..."),
    ("ODATA_USER",      "OData User",     False, ""),
    ("ODATA_PASSWORD",  "OData Password", True,  ""),
]
_MODEL_FIELDS = [
    ("CLAUDE_LLM_MODEL",     "Claude LLM Model",  False, "anthropic--claude-4.6-sonnet"),
    ("GEMINI_LLM_MODEL",     "Gemini LLM Model",  False, "gemini-2.5-pro"),
    ("OPENAI_LLM_MODEL",     "OpenAI LLM Model",  False, "gpt-4o"),
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
        ctk.CTkLabel(hdr, text=_("Config"),
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(hdr, text=_("Save Config"), width=110, height=32,
                      command=self._save).pack(side="right")
        self._save_label = ctk.CTkLabel(hdr, text="", text_color="gray")
        self._save_label.pack(side="right", padx=(0, 10))

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        work_dir_card = self._build_work_dir_card(scroll)
        work_dir_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=6)

        groups = [
            ("SAP AI Core",  _AI_CORE_FIELDS),
            ("HANA Cloud",   _HANA_FIELDS),
            (_("Proc Params"), _PROC_FIELDS),
            (_("AI Models"),   _MODEL_FIELDS),
            (_("OData Verify"), _VERIFY_FIELDS),
        ]

        row = 1
        col = 0
        for group_name, fields in groups:
            card = self._make_group_card(scroll, group_name, fields)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            col += 1
            if col > 1:
                col = 0
                row += 1

    def _build_work_dir_card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=_("Work Directory"),
                     font=ctk.CTkFont(weight="bold", size=13)).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(10, 4))

        self._work_dir_var = ctk.StringVar(value=str(get_work_dir() or ""))
        entry = ctk.CTkEntry(card, textvariable=self._work_dir_var,
                             font=ctk.CTkFont(size=11), state="readonly")
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(12, 4), pady=4)

        ctk.CTkButton(card, text=_("Browse"), width=70, height=28,
                      command=self._browse_work_dir).grid(
            row=1, column=2, padx=(0, 12), pady=4)

        ctk.CTkLabel(card, text="").grid(row=2, column=0, pady=(0, 4))
        return card

    def _browse_work_dir(self):
        chosen = filedialog.askdirectory(title=_("Select Work Directory"))
        if chosen:
            path = Path(chosen)
            try:
                test = path / ".write_test"
                test.touch()
                test.unlink()
            except OSError:
                messagebox.showerror(_("Error"), _("Cannot write to: {}").format(path))
                return
            set_work_dir(path)
            self._work_dir_var.set(str(path))

    def _make_group_card(self, parent, title: str, fields: list) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont(weight="bold", size=13)).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 4))

        for i, (key, label, sensitive, placeholder) in enumerate(fields, start=1):
            ctk.CTkLabel(card, text=_(label), anchor="w",
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

        ctk.CTkLabel(card, text="").grid(
            row=len(fields) + 1, column=0, pady=(0, 4))
        return card

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        env_path = get_base_path() / ".env"
        if not env_path.exists():
            messagebox.showerror(_("Error"), _(".env file not found: {}").format(env_path))
            return

        changed = 0
        for key, entry in self._entries.items():
            val = entry.get()
            if val:
                set_key(str(env_path), key, val)
                os.environ[key] = val
                changed += 1

        self._save_label.configure(
            text=_("Saved {} items ✓").format(changed), text_color="#81c784")
        self.after(3000, lambda: self._save_label.configure(text="", text_color="gray"))
