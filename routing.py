"""Bounded, visible fallback using only services the user configured."""
from core import ApiError

CHAT_ORDER=("groq","gemini","openrouter","meta")
STT_ORDER=("groq","gemini","elevenlabs","fish")
NAMES={"groq":"Groq","gemini":"Gemini","openrouter":"OpenRouter","meta":"Meta Llama","elevenlabs":"ElevenLabs","fish":"Fish Audio"}


def configured_order(primary, order, keys, fallback=True):
    wanted=[primary]+[p for p in order if p!=primary] if fallback else [primary]
    return [p for p in wanted if keys.get(p)]


def run_fallback(order, operation, cancelled):
    failures=[]
    if not order:raise ApiError("No key saved for this feature. Add a complete key in Settings and use Test connection.",category="missing")
    for provider in order:
        if cancelled.is_set():raise ApiError("Conversation interrupted.",category="cancelled")
        try:
            result=operation(provider)
            if cancelled.is_set():raise ApiError("Conversation interrupted.",category="cancelled")
            return result,provider,failures
        except ApiError as exc:
            if exc.category=="cancelled":raise
            failures.append(str(exc))
    raise ApiError("No configured service could finish. "+" | ".join(failures),category="all_failed")
