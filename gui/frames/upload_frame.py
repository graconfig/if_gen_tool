"""
Upload page: knowledge base Excel upload to HANA CUSTFIELDS.
"""

import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from utils.i18n import _
from core.config import ConfigurationManager


class UploadFrame(ctk.CTkFrame):
    POLL_MS = 150

    def __init__(self, parent, config_manager: ConfigurationManager,
                 log_queue: queue.Queue):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.config_manager = config_manager
        self.log_queue = log_queue

        self._upload_path: Path | None = None
        self._worker: threading.Thread | None = None

        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text=_("KB Upload"),
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        # ── File selection card
        card = ctk.CTkFrame(self)
        card.grid(row=1, column=0, sticky="ew", padx=16, pady=4)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=_("Upload File")).grid(
            row=0, column=0, padx=(12, 6), pady=10, sticky="w")
        self._file_label = ctk.CTkLabel(card, text=_("Not selected"), text_color="gray",
                                        anchor="w")
        self._file_label.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkButton(card, text=_("Browse"), width=90,
                      command=self._pick_file).grid(
            row=0, column=2, padx=(4, 12), pady=10)

        ctk.CTkLabel(card, text=_("Sheet Name\n(auto if blank)")).grid(
            row=1, column=0, padx=(12, 6), pady=(4, 10), sticky="w")
        self._sheet_entry = ctk.CTkEntry(card, placeholder_text=_("正本 (auto-detect)"))
        self._sheet_entry.grid(row=1, column=1, columnspan=2, sticky="ew",
                               padx=(4, 12), pady=(4, 10))

        # ── Upload mode
        mode_card = ctk.CTkFrame(self)
        mode_card.grid(row=2, column=0, sticky="ew", padx=16, pady=4)

        ctk.CTkLabel(mode_card, text=_("Upload Mode"),
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(10, 4))

        import os
        current_mode = os.getenv("UPLOAD_MODE", "overwrite")
        self._mode_var = ctk.StringVar(value=current_mode)
        for i, (val, label) in enumerate([
            ("overwrite", _("Overwrite (delete old data)")),
            ("upsert",    _("Upsert (keep old data)")),
        ]):
            ctk.CTkRadioButton(mode_card, text=label, variable=self._mode_var,
                               value=val).grid(row=1, column=i, padx=12, pady=(0, 10),
                                               sticky="w")

        # ── Action button + stats
        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="e", padx=16, pady=8)

        self._upload_btn = ctk.CTkButton(
            action_row, text=_("▶  Start Upload"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40, width=140, command=self._start_upload)
        self._upload_btn.pack(side="right")

        self._stats_label = ctk.CTkLabel(
            action_row, text="", text_color="gray")
        self._stats_label.pack(side="right", padx=(0, 12))

        # ── Log area
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(4, 12))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(log_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 2))
        ctk.CTkLabel(hdr, text=_("Upload Log"),
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(hdr, text=_("Clear"), width=50, height=24,
                      fg_color="transparent", border_width=1,
                      command=self._clear_log).pack(side="right")

        self._log_box = ctk.CTkTextbox(
            log_frame, font=ctk.CTkFont(family="Courier", size=11),
            wrap="word", state="disabled")
        self._log_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self._status_label = ctk.CTkLabel(log_frame, text="", text_color="gray")
        self._status_label.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 6))

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _pick_file(self):
        path = filedialog.askopenfilename(
            title=_("Select Upload Excel"),
            filetypes=[(_("Excel Files"), "*.xlsx *.xls"), (_("All Files"), "*.*")])
        if path:
            self._upload_path = Path(path)
            self._file_label.configure(text=self._upload_path.name, text_color="white")

    def _start_upload(self):
        if not self._upload_path or not self._upload_path.exists():
            messagebox.showwarning(_("No File"), _("Please select an Excel file to upload."))
            return

        self._upload_btn.configure(state="disabled")
        self._status_label.configure(text=_("Connecting to HANA..."), text_color="#4fc3f7")
        self._stats_label.configure(text="")

        import os
        os.environ["UPLOAD_MODE"] = self._mode_var.get()

        self._worker = threading.Thread(target=self._run_upload, daemon=True)
        self._worker.start()
        self.after(self.POLL_MS, self._poll)

    def _run_upload(self):
        from hana.hana_conn import HANADBClient
        from utils.sap_logger import logger
        from datetime import datetime

        sheet = self._sheet_entry.get().strip() or None
        log_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        log_filename = logger.get_excel_log_filename(log_name)

        try:
            hana = HANADBClient()
            hana.connect()
            self.log_queue.put("__STATUS__ " + _("Uploading..."))
            stats = hana.upload_custfields_from_excel(
                excel_path=str(self._upload_path),
                sheet_name=sheet,
                log_filename=log_filename,
            )
            hana.close()
            self.log_queue.put(f"__UPLOAD_DONE__ {stats}")
        except Exception as e:
            self.log_queue.put(f"__ERROR__ {e}")

    def _poll(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg.startswith("__UPLOAD_DONE__"):
                    import ast
                    stats = ast.literal_eval(msg[15:].strip())
                    self._on_done(stats)
                    return
                elif msg.startswith("__ERROR__"):
                    err = msg[9:]
                    self._upload_btn.configure(state="normal")
                    self._status_label.configure(
                        text=_("Error: {}").format(err[:60]), text_color="#ef9a9a")
                    messagebox.showerror(_("Upload Failed"), str(err))
                    return
                elif msg.startswith("__STATUS__"):
                    self._status_label.configure(
                        text=msg[11:], text_color="#4fc3f7")
                else:
                    self._append_log(msg)
        except Exception:
            pass

        if self._worker and self._worker.is_alive():
            self.after(self.POLL_MS, self._poll)
        else:
            self._upload_btn.configure(state="normal")

    def _on_done(self, stats: dict):
        self._upload_btn.configure(state="normal")
        inserted = stats.get("inserted", 0)
        updated = stats.get("updated", 0)
        skipped = stats.get("skipped", 0)
        errors = stats.get("errors", 0)
        summary = _("Inserted {inserted} | Updated {updated} | Skipped {skipped} | Errors {errors}").format(
            inserted=inserted, updated=updated, skipped=skipped, errors=errors)
        self._stats_label.configure(text=summary, text_color="#81c784")
        self._status_label.configure(text=_("Upload done ✓"), text_color="#81c784")
        messagebox.showinfo(_("Upload Done"), summary)

    def _append_log(self, msg: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
