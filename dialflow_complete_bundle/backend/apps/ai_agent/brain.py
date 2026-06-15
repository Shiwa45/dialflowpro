"""
The AI 'brain' helpers.

Two responsibilities:
  1. assemble_system_prompt(agent): build the full instruction the LLM gets,
     combining persona + behaviour + the active knowledge base. This is what
     "training on product details" actually means in production: retrieval
     grounding, not weight fine-tuning.
  2. retrieve_context(agent, query): pick the most relevant knowledge chunks for
     a given caller utterance. Phase 1 ships a lexical fallback so it works with
     zero extra infrastructure; Phase 2 swaps in embeddings (see tasks.py) with
     the same signature, so the media worker doesn't change.

Keeping both here means the LiveKit worker (Phase 2) imports one module and the
admin "preview prompt" endpoint shows exactly what the live agent will use.
"""
from __future__ import annotations

import re
from typing import List


def assemble_system_prompt(agent) -> str:
    """Compose the complete system prompt the LLM receives at call start."""
    parts: List[str] = []

    persona = agent.persona_name or "Assistant"
    parts.append(
        f"You are {persona}, a voice assistant answering phone calls for a "
        f"business. Speak naturally and concisely, as in a real phone "
        f"conversation. Keep replies short unless the caller asks for detail."
    )

    lang = agent.primary_language
    if lang and lang != "unknown":
        parts.append(
            f"Respond in the caller's language. Your primary language is "
            f"'{lang}'. You may handle code-mixed speech (e.g. Hinglish) "
            f"naturally."
        )

    if agent.system_prompt:
        parts.append(agent.system_prompt.strip())

    # Behaviour / escalation guidance the LLM should respect via tool calls.
    rules = []
    if agent.allow_human_transfer:
        rules.append(
            "If the caller explicitly asks for a human, or you are not "
            "confident you can help, call the `transfer_to_human` tool."
        )
    if agent.allow_callback:
        rules.append(
            "If no human agent is available, offer to schedule a callback and "
            "call the `schedule_callback` tool with the caller's preferred time."
        )
    rules.append(
        "Never invent product details, prices, or policies. If the knowledge "
        "below does not cover the question, say you will check and offer a "
        "human or callback."
    )
    if rules:
        parts.append("Rules:\n- " + "\n- ".join(rules))

    # Knowledge base
    kb = _format_knowledge(agent)
    if kb:
        parts.append("Business knowledge you can rely on:\n" + kb)

    return "\n\n".join(parts)


def _format_knowledge(agent) -> str:
    items = agent.knowledge_items.filter(is_active=True).order_by("source_type", "title")
    lines: List[str] = []
    for it in items:
        if it.source_type == "product":
            attrs = ", ".join(f"{k}: {v}" for k, v in (it.product_attributes or {}).items())
            price = f" — price {it.product_price}" if it.product_price else ""
            head = it.product_name or it.title
            lines.append(f"[Product] {head}{price}. {it.content}"
                         + (f" ({attrs})" if attrs else ""))
        elif it.source_type == "faq":
            lines.append(f"[FAQ] {it.title}: {it.content}")
        else:
            lines.append(f"[{it.get_source_type_display()}] {it.title}: {it.content}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  Retrieval — Phase 1 lexical, Phase 2 embedding (same signature)
# --------------------------------------------------------------------------- #
_WORD = re.compile(r"\w+")


def _tokens(text: str) -> set[str]:
    return set(w.lower() for w in _WORD.findall(text or ""))


def retrieve_context(agent, query: str, top_k: int = 4) -> List[str]:
    """
    Return up to `top_k` knowledge snippets most relevant to `query`.

    If embedded chunks exist (Phase 2), score by cosine similarity; otherwise
    fall back to lexical overlap over active knowledge items. Either way the
    return type is a list of plain strings the LLM can be shown.
    """
    chunks = list(agent.knowledge_chunks.all())
    q_emb = None
    if chunks and any(c.embedding for c in chunks):
        try:
            from .tasks import embed_text  # Phase 2 provides this
            q_emb = embed_text(query)
        except Exception:
            q_emb = None

    if q_emb is not None:
        scored = []
        for c in chunks:
            if not c.embedding:
                continue
            scored.append((_cosine(q_emb, c.embedding), c.text))
        scored.sort(reverse=True)
        return [t for _, t in scored[:top_k]]

    # Lexical fallback over items
    q = _tokens(query)
    scored = []
    for it in agent.knowledge_items.filter(is_active=True):
        text = f"{it.title} {it.content} {it.product_name}"
        overlap = len(q & _tokens(text))
        if overlap:
            scored.append((overlap, f"{it.title}: {it.content}"))
    scored.sort(reverse=True)
    return [t for _, t in scored[:top_k]]


def _cosine(a, b) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
