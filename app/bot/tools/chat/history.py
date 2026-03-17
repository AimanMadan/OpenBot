from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

MAX_TURNS_PER_CHANNEL = 200
TOKEN_LIMIT = 128_000
AUTO_SUMMARIZE_THRESHOLD = 100_000


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ChannelHistory:
    messages: deque[Message] = field(
        default_factory=lambda: deque(maxlen=MAX_TURNS_PER_CHANNEL)
    )
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    last_input_tokens: int = 0


_store: dict[int, ChannelHistory] = {}


def _get_channel(channel_id: int) -> ChannelHistory:
    history = _store.get(channel_id)
    if history is None:
        history = ChannelHistory()
        _store[channel_id] = history
    return history


def append_user_message(channel_id: int, content: str) -> None:
    ch = _get_channel(channel_id)
    ch.messages.append(Message(role="user", content=content))
    ch.last_updated = datetime.now(timezone.utc)


def append_bot_message(channel_id: int, content: str) -> None:
    ch = _get_channel(channel_id)
    ch.messages.append(Message(role="assistant", content=content))
    ch.last_updated = datetime.now(timezone.utc)


def record_token_usage(channel_id: int, input_tokens: int, output_tokens: int) -> None:
    ch = _get_channel(channel_id)
    ch.total_input_tokens += input_tokens
    ch.total_output_tokens += output_tokens
    ch.last_input_tokens = input_tokens


def should_auto_summarize(channel_id: int) -> bool:
    ch = _store.get(channel_id)
    if ch is None:
        return False
    return ch.last_input_tokens >= AUTO_SUMMARIZE_THRESHOLD


def get_history(channel_id: int) -> list[Message]:
    return list(_get_channel(channel_id).messages)


def clear_history(channel_id: int) -> None:
    if channel_id in _store:
        del _store[channel_id]


def history_stats(channel_id: int) -> dict:
    ch = _store.get(channel_id)
    if ch is None or len(ch.messages) == 0:
        return {
            "total": 0,
            "user": 0,
            "assistant": 0,
            "last_updated": None,
            "last_input_tokens": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "token_limit": TOKEN_LIMIT,
        }

    user_count = sum(1 for m in ch.messages if m.role == "user")
    assistant_count = sum(1 for m in ch.messages if m.role == "assistant")
    return {
        "total": len(ch.messages),
        "user": user_count,
        "assistant": assistant_count,
        "last_updated": ch.last_updated,
        "last_input_tokens": ch.last_input_tokens,
        "total_input_tokens": ch.total_input_tokens,
        "total_output_tokens": ch.total_output_tokens,
        "token_limit": TOKEN_LIMIT,
    }


def format_history_as_text(channel_id: int) -> str:
    """Format the stored history into a readable string for LLM input."""
    messages = get_history(channel_id)
    if not messages:
        return ""
    lines = []
    for msg in messages:
        prefix = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{prefix}: {msg.content}")
    return "\n".join(lines)
