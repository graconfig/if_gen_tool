"""
Token使用统计
"""

import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import translation function
from utils.i18n import _

# Thread-local storage for per-thread file context
_thread_local = threading.local()


@dataclass
class TokenUsage:
    embedding_tokens: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_total_tokens: int = 0

    def add_embedding(self, tokens: int):
        self.embedding_tokens += tokens

    def add_llm(
        self, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0
    ):
        self.llm_input_tokens += input_tokens
        self.llm_output_tokens += output_tokens
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens

        self.llm_total_tokens += total_tokens


class TokenTracker:
    def __init__(self, base_dir: Path):
        self.token_dir = base_dir / "tokens"
        self.token_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()

        self.usage = TokenUsage()
        self.provider_usage = {}
        self.file_usage = {}  # Track usage per file

        self.current_provider = None

    def set_provider(self, provider: str, model: str = None):
        with self._lock:
            self.current_provider = provider
            if provider not in self.provider_usage:
                self.provider_usage[provider] = TokenUsage()

    def set_current_file(self, filename: str):
        """Set the current file being processed for per-file token tracking (thread-safe)."""
        with self._lock:
            # Use thread-local storage for current file
            _thread_local.current_file = filename
            if filename not in self.file_usage:
                self.file_usage[filename] = TokenUsage()

    def get_current_file(self) -> Optional[str]:
        """Get the current file for this thread."""
        return getattr(_thread_local, "current_file", None)

    def track_embedding(self, tokens: int, provider: str = None):
        if tokens <= 0:
            return

        with self._lock:
            provider = provider or self.current_provider
            self.usage.add_embedding(tokens)
            if provider and provider in self.provider_usage:
                self.provider_usage[provider].add_embedding(tokens)
            # Track per-file usage using thread-local current file
            current_file = self.get_current_file()
            if current_file and current_file in self.file_usage:
                self.file_usage[current_file].add_embedding(tokens)

    def track_llm(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        provider: str = None,
    ):
        if input_tokens <= 0 and output_tokens <= 0:
            return

        with self._lock:
            provider = provider or self.current_provider
            self.usage.add_llm(input_tokens, output_tokens, total_tokens)
            if provider and provider in self.provider_usage:
                self.provider_usage[provider].add_llm(input_tokens, output_tokens)
            # Track per-file usage using thread-local current file
            current_file = self.get_current_file()
            if current_file and current_file in self.file_usage:
                self.file_usage[current_file].add_llm(input_tokens, output_tokens)

    def get_usage(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "usage": asdict(self.usage),
                "provider_usage": {
                    k: asdict(v) for k, v in self.provider_usage.items()
                },
                "file_usage": {k: asdict(v) for k, v in self.file_usage.items()},
                "timestamp": datetime.now().isoformat(),
            }

    def save_usage(self, additional_info: Dict[str, Any] = None) -> Path:
        data = self.get_usage()
        if additional_info:
            data.update(additional_info)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = self.token_dir / f"session_{timestamp}.json"
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return session_file

    # def print_summary(self):
    #     """打印使用摘要"""
    #     data = self.get_usage()
    #     usage = data["usage"]
    #
    #     print("\n" + "=" * 50)
    #     print(_("📊 TOKEN USAGE SUMMARY"))
    #     print("=" * 50)
    #     print(_("Embedding: {:,}").format(usage["embedding_tokens"]))
    #     print(_("LLM Input: {:,}").format(usage["llm_input_tokens"]))
    #     print(_("LLM Output: {:,}").format(usage["llm_output_tokens"]))
    #     print(_("LLM Total: {:,}").format(usage["llm_total_tokens"]))
    #     print(
    #         _("Total: {:,}").format(
    #             usage["llm_input_tokens"]
    #             + usage["llm_output_tokens"]
    #             + usage["embedding_tokens"]
    #         )
    #     )
    #
    #     if data["provider_usage"]:
    #         print("\n" + _("🤖 By Provider:"))
    #         for provider, p_usage in data["provider_usage"].items():
    #             total = (
    #                 p_usage["embedding_tokens"]
    #                 + p_usage["llm_input_tokens"]
    #                 + p_usage["llm_output_tokens"]
    #             )
    #             print(_("  {}: {:,}").format(provider, total))
    #
    #     print("=" * 50)


_tracker: Optional[TokenTracker] = None


def initialize_token_tracker(base_dir: Path) -> TokenTracker:
    global _tracker
    _tracker = TokenTracker(base_dir)
    return _tracker


def set_current_provider(provider: str, model: str = None):
    if _tracker:
        _tracker.set_provider(provider, model)


def set_current_file(filename: str):
    """Set the current file being processed for per-file token tracking (thread-safe)."""
    if _tracker:
        _tracker.set_current_file(filename)


def track_embedding_tokens(tokens: int, provider: str = None):
    if _tracker:
        _tracker.track_embedding(tokens, provider)


def track_llm_tokens(
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: int = 0,
    provider: str = None,
):
    if _tracker:
        _tracker.track_llm(input_tokens, output_tokens, total_tokens, provider)


def save_and_print_usage(additional_info: Dict[str, Any] = None) -> Optional[Path]:
    if _tracker:
        file_path = _tracker.save_usage(additional_info)
        # _tracker.print_summary()
        return file_path
    return None


def save_file_token_usage(
    filename: str, additional_info: Dict[str, Any] = None
) -> Optional[Path]:
    """Save token usage for a specific file."""
    if _tracker:
        with _tracker._lock:
            # Get the file-specific usage
            if filename in _tracker.file_usage:
                file_usage = _tracker.file_usage[filename]

                # Create file-specific data
                data = {
                    "usage": asdict(file_usage),
                    "timestamp": datetime.now().isoformat(),
                }

                if additional_info:
                    data.update(additional_info)

                # Save to file-specific token file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_token_file = _tracker.token_dir / f"{filename}_{timestamp}.json"
                with open(file_token_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                return file_token_file
    return None
