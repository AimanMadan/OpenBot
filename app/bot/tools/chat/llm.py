import logging

from openai import OpenAI

from config import settings
from . import history

log = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key.get_secret_value())

SYSTEM_PROMPT = (
    "You are OpenBot, a helpful and opinionated Discord assistant. "
    "You speak clearly, concisely, and casually, using simple language and short paragraphs. "
    "You are given the most recent message plus recent conversation history for this channel; "
    "use that history to maintain context, remember what the user is working on, "
    "and avoid repeating yourself. "
    "You can answer questions, help with coding and debugging, and respond to general chat "
    "in a friendly way. "
    "You never claim to be a human, politician, or celebrity, and you never pretend "
    "to be any real person. "
    "You avoid long disclaimers and over-explaining unless the user asks for more detail. "
    "Always prioritize being accurate, safe, and useful to the user.\n\n"
    "You have the following capabilities that users can ask about:\n"
    "• AI Chat — Users prefix a message with ! to talk to you. "
    "You remember recent conversation per channel for contextual replies.\n"
    "• Conversation Context — Per-channel message history is kept in memory "
    "(resets on bot restart). You track token usage against a 128k context window "
    "and auto-summarize when usage reaches 100k tokens, so conversations can run "
    "indefinitely without hitting the limit.\n"
    "  /context_status — Show messages stored, token usage, context window percentage, "
    "and session totals.\n"
    "  /context_clear — Clear all conversation history for the current channel.\n"
    "  /context_summarize — Summarize the conversation, replace history with the summary, "
    "and start fresh.\n"
    "• Music Playback — Search YouTube and stream audio into a voice channel "
    "with a full queue system.\n"
    "  /play <query> — Search and play a track, or add it to the queue.\n"
    "  /skip — Skip to the next track in the queue.\n"
    "  /pause — Pause the current track.\n"
    "  /resume — Resume a paused track.\n"
    "  /stop — Stop playback, clear the queue, and disconnect.\n"
    "  /queue — Show the currently playing track and upcoming queue."
)

SUMMARIZE_PROMPT = (
    "Summarize the following Discord conversation into concise bullet points. "
    "Focus on key topics discussed, decisions made, and any unresolved questions. "
    "Your summary MUST use no more than {max_tokens} tokens — roughly half the "
    "current conversation length. Be as dense and information-rich as possible "
    "within that budget."
)


def _record_usage(channel_id: int, resp) -> None:
    if resp.usage is None:
        return
    history.record_token_usage(
        channel_id, resp.usage.input_tokens, resp.usage.output_tokens
    )


def response(channel_id: int, message: str) -> str:
    history_text = history.format_history_as_text(channel_id)

    if history_text:
        full_input = f"{history_text}\nUser: {message}"
    else:
        full_input = message

    history.append_user_message(channel_id, message)

    resp = client.responses.create(
        model="gpt-5-nano",
        instructions=SYSTEM_PROMPT,
        input=full_input,
    )
    reply = resp.output_text

    history.append_bot_message(channel_id, reply)
    _record_usage(channel_id, resp)

    if history.should_auto_summarize(channel_id):
        log.info(
            "Auto-summarizing channel %s (tokens: %d)",
            channel_id,
            resp.usage.input_tokens,
        )
        summarize(channel_id)

    return reply


def summarize(channel_id: int) -> str | None:
    """Summarize the conversation history for a channel. Returns None if no history."""
    history_text = history.format_history_as_text(channel_id)
    if not history_text:
        return None

    stats = history.history_stats(channel_id)
    current_tokens = stats["last_input_tokens"] or stats["total_input_tokens"]
    max_tokens = max(current_tokens // 2, 256)

    resp = client.responses.create(
        model="gpt-5-nano",
        instructions=SUMMARIZE_PROMPT.format(max_tokens=max_tokens),
        max_output_tokens=max_tokens,
        input=history_text,
    )
    summary = resp.output_text

    history.clear_history(channel_id)
    history.append_bot_message(channel_id, f"[Summary] {summary}")
    _record_usage(channel_id, resp)

    return summary
