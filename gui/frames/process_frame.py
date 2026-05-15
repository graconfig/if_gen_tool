"""
Process page: file list, options, real-time log, token stats.
"""

import queue
import shutil
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from utils.i18n import _
from core.config import ConfigurationManager
from core.consts import AIProvider, Languages, Directories, FileExtensions


class ProcessFrame(ctk.CTkFrame):
    POLL_MS = 100

    def __init__(self, parent, config_manager: ConfigurationManager,
                 language: str, log_queue: queue.Queue):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.config_manager = config_manager
        self.language = language
        self.log_queue = log_queue

        self._processing = False
        self._worker: threading.Thread | None = None

        self._base_dir = self._get_base_dir()
        self._data_dir = self._base_dir / "data"
        self._input_dir = self._data_dir / Directories.EXCEL_INPUT

        self._build_ui()
        self._refresh_file_list()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_base_dir(self) -> Path:
        import sys
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(__file__).parent.parent.parent

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top: title
        title = ctk.CTkLabel(self, text=_("IF File Processing"),
                             font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 8))

        # ── Left: file list panel
        self._file_panel = ctk.CTkFrame(self)
        self._file_panel.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=8)
        self._file_panel.grid_columnconfigure(0, weight=1)
        self._file_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self._file_panel, text=_("Pending Files"),
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 4))

        self._file_scroll = ctk.CTkScrollableFrame(self._file_panel, height=160)
        self._file_scroll.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=4)
        self._file_scroll.grid_columnconfigure(0, weight=1)

        btn_row = ctk.CTkFrame(self._file_panel, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 10))
        ctk.CTkButton(btn_row, text=_("+ Add Files"), width=110,
                      command=self._add_files).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text=_("Open Dir"), width=90, fg_color="transparent",
                      border_width=1, command=self._open_input_dir).pack(side="left")
        ctk.CTkButton(btn_row, text=_("Refresh"), width=60, fg_color="transparent",
                      border_width=1, command=self._refresh_file_list).pack(side="right")

        # ── Right: options panel
        self._opt_panel = ctk.CTkFrame(self)
        self._opt_panel.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=8)
        self._opt_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._opt_panel, text=_("Options"),
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 6))

        ctk.CTkLabel(self._opt_panel, text=_("Language")).grid(
            row=1, column=0, sticky="w", padx=12, pady=(4, 0))
        self._lang_var = ctk.StringVar(value=self.language)
        self._lang_menu = ctk.CTkOptionMenu(
            self._opt_panel, values=Languages.SUPPORTED, variable=self._lang_var)
        self._lang_menu.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(self._opt_panel, text=_("AI Provider")).grid(
            row=3, column=0, sticky="w", padx=12, pady=(4, 0))
        self._provider_var = ctk.StringVar(
            value=self.config_manager.get_model_config()["default_provider"])
        self._provider_menu = ctk.CTkOptionMenu(
            self._opt_panel, values=AIProvider.ALL_PROVIDERS,
            variable=self._provider_var)
        self._provider_menu.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 16))

        self._start_btn = ctk.CTkButton(
            self._opt_panel, text=_("▶  Start"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40, command=self._start_processing)
        self._start_btn.grid(row=5, column=0, sticky="ew", padx=12, pady=4)

        self._stop_btn = ctk.CTkButton(
            self._opt_panel, text=_("■  Stop"),
            fg_color="#b03030", hover_color="#8b1a1a",
            height=36, command=self._request_stop, state="disabled")
        self._stop_btn.grid(row=6, column=0, sticky="ew", padx=12, pady=4)

        # Status label
        self._status_label = ctk.CTkLabel(
            self._opt_panel, text=_("Ready"), text_color="gray",
            wraplength=150, justify="left")
        self._status_label.grid(row=7, column=0, sticky="w", padx=12, pady=(8, 0))

        # ── Bottom: log area (spans both columns)
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew",
                       padx=16, pady=(0, 8))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        ctk.CTkLabel(log_header, text=_("Live Log"),
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(log_header, text=_("Clear"), width=50, height=24,
                      fg_color="transparent", border_width=1,
                      command=self._clear_log).pack(side="right")

        self._log_box = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Courier", size=11),
                                       wrap="word", state="disabled")
        self._log_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))

        # Progress bar
        self._progress = ctk.CTkProgressBar(log_frame)
        self._progress.set(0)
        self._progress.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 4))

        # Token stats bar
        self._token_label = ctk.CTkLabel(
            log_frame, text=_("Token: —"),
            font=ctk.CTkFont(size=11), text_color="gray")
        self._token_label.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 6))

    # ── File list management ─────────────────────────────────────────────────

    def _refresh_file_list(self):
        for widget in self._file_scroll.winfo_children():
            widget.destroy()

        self._input_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(self._input_dir.glob(f"*{FileExtensions.XLSX}"))
        files += sorted(self._input_dir.glob("*.xls"))

        if not files:
            ctk.CTkLabel(self._file_scroll, text=_("No files"),
                         text_color="gray").grid(row=0, column=0, pady=8)
            return

        for i, fp in enumerate(files):
            row_frame = ctk.CTkFrame(self._file_scroll, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row_frame, text=fp.name, anchor="w").grid(
                row=0, column=0, sticky="ew", padx=(4, 8))
            ctk.CTkButton(row_frame, text=_("Delete"), width=48, height=24,
                          fg_color="#7a2222", hover_color="#5a1111",
                          command=lambda p=fp: self._delete_file(p)).grid(
                row=0, column=1)

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title=_("Select Excel Files"),
            filetypes=[(_("Excel Files"), "*.xlsx *.xls"), (_("All Files"), "*.*")])
        if not paths:
            return
        self._input_dir.mkdir(parents=True, exist_ok=True)
        for p in paths:
            shutil.copy2(p, self._input_dir / Path(p).name)
        self._refresh_file_list()

    def _delete_file(self, path: Path):
        if messagebox.askyesno(_("Confirm Delete"), _("Delete file {}?").format(path.name)):
            path.unlink(missing_ok=True)
            self._refresh_file_list()

    def _open_input_dir(self):
        import os
        os.startfile(str(self._input_dir))

    # ── Processing ───────────────────────────────────────────────────────────

    def _set_processing(self, active: bool):
        self._processing = active
        state = "disabled" if active else "normal"
        self._start_btn.configure(state=state)
        self._lang_menu.configure(state=state)
        self._provider_menu.configure(state=state)
        self._stop_btn.configure(state="normal" if active else "disabled")
        if active:
            self._progress.configure(mode="indeterminate")
            self._progress.start()
        else:
            self._progress.stop()
            self._progress.configure(mode="determinate")
            self._progress.set(1.0)

    def _start_processing(self):
        files = list(self._input_dir.glob(f"*{FileExtensions.XLSX}"))
        files += list(self._input_dir.glob("*.xls"))
        if not files:
            messagebox.showwarning(_("No Files"), _("Please add Excel files first."))
            return

        self._set_processing(True)
        self._status_label.configure(text=_("Processing..."), text_color="#4fc3f7")
        self._progress.set(0)

        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._run_all, daemon=True)
        self._worker.start()
        self.after(self.POLL_MS, self._poll)

    def _request_stop(self):
        if hasattr(self, "_stop_event"):
            self._stop_event.set()
        self._status_label.configure(text=_("Stopping..."), text_color="orange")

    def _run_all(self):
        from main import (
            process_single_excel_file,
            setup_directories,
            get_base_path,
        )
        from utils.token_statistics import initialize_token_tracker
        from hana.hana_conn import HANADBClient

        try:
            base_dir = get_base_path()
            data_dir = setup_directories()
            initialize_token_tracker(base_dir)

            hana_client = HANADBClient()
            hana_client.connect()

            start_time = datetime.now()
            files = sorted(data_dir.joinpath(Directories.EXCEL_INPUT).glob(f"*{FileExtensions.XLSX}"))
            files += sorted(data_dir.joinpath(Directories.EXCEL_INPUT).glob("*.xls"))

            for fp in files:
                if self._stop_event.is_set():
                    self.log_queue.put("__STATUS__ " + _("Stopped"))
                    break
                self.log_queue.put("__STATUS__ " + _("Processing: {}").format(fp.name))
                process_single_excel_file(
                    fp, data_dir, self.config_manager,
                    self._lang_var.get(), self._provider_var.get(),
                    start_time, hana_client,
                )

            hana_client.close()
            self.log_queue.put("__DONE__")
        except Exception as e:
            self.log_queue.put(f"__ERROR__ {e}")

    # ── Polling ──────────────────────────────────────────────────────────────

    def _poll(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg.startswith("__DONE__"):
                    self._on_done(success=True)
                    self._update_token_stats()
                    return
                elif msg.startswith("__ERROR__"):
                    err = msg[9:]
                    self._on_done(success=False, error=err)
                    return
                elif msg.startswith("__STATUS__"):
                    self._status_label.configure(text=msg[11:], text_color="#4fc3f7")
                else:
                    self._append_log(msg)
        except Exception:
            pass

        if self._worker and self._worker.is_alive():
            self._update_token_stats()
            self.after(self.POLL_MS, self._poll)
        else:
            self._on_done(success=True)

    def _on_done(self, success: bool, error: str = ""):
        self._set_processing(False)
        self._refresh_file_list()
        self._update_token_stats()
        if success:
            self._status_label.configure(text=_("Done ✓"), text_color="#81c784")
            messagebox.showinfo(_("Done"), _("All files processed. Output saved to data/excel_output/"))
        else:
            self._status_label.configure(text=_("Error: {}").format(error[:40]), text_color="#ef9a9a")
            messagebox.showerror(_("Processing Failed"), str(error))

    # ── Log helpers ──────────────────────────────────────────────────────────

    def _append_log(self, msg: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _update_token_stats(self):
        try:
            from utils.token_statistics import _tracker
            if _tracker is None:
                return
            data = _tracker.get_usage()["usage"]
            total = data["llm_input_tokens"] + data["llm_output_tokens"] + data["embedding_tokens"]
            self._token_label.configure(
                text=(_("Token:  Embed {embed} | LLM In {in_} | LLM Out {out} | Total {total}").format(
                    embed=f"{data['embedding_tokens']:,}",
                    in_=f"{data['llm_input_tokens']:,}",
                    out=f"{data['llm_output_tokens']:,}",
                    total=f"{total:,}",
                )))
        except Exception:
            pass
