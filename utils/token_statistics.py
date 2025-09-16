"""
Token使用统计
"""

import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class TokenUsage:
    embedding_tokens: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_total_tokens: int = 0

    def add_embedding(self, tokens: int):
        self.embedding_tokens += tokens

    def add_llm(self, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0):
        self.llm_input_tokens += input_tokens
        self.llm_output_tokens += output_tokens
        self.llm_total_tokens += total_tokens


class TokenTracker:

    def __init__(self, base_dir: Path):
        self.token_dir = base_dir / "tokens"
        self.token_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.usage = TokenUsage()
        self.provider_usage = {}

        self.current_provider = None

    def set_provider(self, provider: str, model: str = None):
        with self._lock:
            self.current_provider = provider
            if provider not in self.provider_usage:
                self.provider_usage[provider] = TokenUsage()

    def track_embedding(self, tokens: int, provider: str = None):
        if tokens <= 0:
            return

        with self._lock:
            provider = provider or self.current_provider
            self.usage.add_embedding(tokens)
            if provider and provider in self.provider_usage:
                self.provider_usage[provider].add_embedding(tokens)

    def track_llm(self, input_tokens: int = 0, output_tokens: int = 0, total_tokens:int = 0, provider: str = None):
        if input_tokens <= 0 and output_tokens <= 0:
            return

        with self._lock:
            provider = provider or self.current_provider
            self.usage.add_llm(input_tokens, output_tokens, total_tokens)
            if provider and provider in self.provider_usage:
                self.provider_usage[provider].add_llm(input_tokens, output_tokens)

    def get_usage(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "session_id": self.session_id,
                "usage": asdict(self.usage),
                "provider_usage": {k: asdict(v) for k, v in self.provider_usage.items()},
                "timestamp": datetime.now().isoformat()
            }

    def save_usage(self, additional_info: Dict[str, Any] = None) -> Path:
        data = self.get_usage()
        if additional_info:
            data.update(additional_info)

        session_file = self.token_dir / f"session_{self.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return session_file

    def print_summary(self):
        """打印使用摘要"""
        data = self.get_usage()
        usage = data['usage']

        print("\n" + "=" * 50)
        print("📊 TOKEN USAGE SUMMARY")
        print("=" * 50)
        print(f"Session: {data['session_id']}")
        print(f"Embedding: {usage['embedding_tokens']:,}")
        print(f"LLM Input: {usage['llm_input_tokens']:,}")
        print(f"LLM Output: {usage['llm_output_tokens']:,}")
        print(f"LLM Total: {usage['llm_total_tokens']:,}")
        print(f"Total: {usage['llm_input_tokens'] + usage['llm_output_tokens'] + usage['embedding_tokens']:,}")

        if data['provider_usage']:
            print("\n🤖 By Provider:")
            for provider, p_usage in data['provider_usage'].items():
                total = p_usage['embedding_tokens'] + p_usage['llm_input_tokens'] + p_usage['llm_output_tokens']
                print(f"  {provider}: {total:,}")

        print("=" * 50)


_tracker: Optional[TokenTracker] = None


def initialize_token_tracker(base_dir: Path) -> TokenTracker:
    global _tracker
    _tracker = TokenTracker(base_dir)
    return _tracker


def set_current_provider(provider: str, model: str = None):
    if _tracker:
        _tracker.set_provider(provider, model)


def track_embedding_tokens(tokens: int, provider: str = None):
    if _tracker:
        _tracker.track_embedding(tokens, provider)


def track_llm_tokens(input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0, provider: str = None):
    if _tracker:
        _tracker.track_llm(input_tokens, output_tokens, total_tokens, provider)


def save_and_print_usage(additional_info: Dict[str, Any] = None) -> Optional[Path]:
    if _tracker:
        file_path = _tracker.save_usage(additional_info)
        # _tracker.print_summary()
        return file_path
    return None
