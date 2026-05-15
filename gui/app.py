"""
Main application window with sidebar navigation and GuiLogHandler.
"""

import logging
import queue

import customtkinter as ctk

from utils.i18n import _
from gui.frames.process_frame import ProcessFrame
from gui.frames.upload_frame import UploadFrame
from gui.frames.config_frame import ConfigFrame

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GuiLogHandler(logging.Handler):
    """Bridges the existing ExcelFileLogger to the GUI log queue."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s",
                                            datefmt="%H:%M:%S"))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put_nowait(msg)
        except Exception:
            pass


class App(ctk.CTk):
    NAV_WIDTH = 160

    def __init__(self, config_manager, language: str):
        super().__init__()

        self.config_manager = config_manager
        self.language = language

        self.title(_("SAP IF Design Generation Tool"))
        self.geometry("1150x720")
        self.minsize(900, 600)

        # Shared log queue injected into the existing logger
        self.log_queue: queue.Queue = queue.Queue()
        self._attach_log_handler()

        self._build_ui()

    def _attach_log_handler(self):
        from utils.sap_logger import logger as app_logger
        handler = GuiLogHandler(self.log_queue)
        app_logger.addHandler(handler)

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._sidebar = ctk.CTkFrame(self, width=self.NAV_WIDTH, corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_rowconfigure(10, weight=1)

        logo = ctk.CTkLabel(self._sidebar, text="IF Gen\nTool",
                            font=ctk.CTkFont(size=16, weight="bold"))
        logo.grid(row=0, column=0, padx=16, pady=(24, 16))

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("process", _("Process")),
            ("upload",  _("KB Upload")),
            ("config",  _("Config")),
        ]
        for i, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self._sidebar, text=label, width=self.NAV_WIDTH - 24,
                corner_radius=8, anchor="w",
                command=lambda k=key: self._show_frame(k),
            )
            btn.grid(row=i, column=0, padx=12, pady=4)
            self._nav_buttons[key] = btn

        # Content area
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # Instantiate frames
        self._frames: dict[str, ctk.CTkFrame] = {
            "process": ProcessFrame(self._content, self.config_manager,
                                    self.language, self.log_queue),
            "upload":  UploadFrame(self._content, self.config_manager,
                                   self.log_queue),
            "config":  ConfigFrame(self._content, self.config_manager),
        }
        for frame in self._frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self._show_frame("process")

    def _show_frame(self, key: str):
        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color=("gray75", "gray25") if k == key else "transparent")
        self._frames[key].tkraise()
