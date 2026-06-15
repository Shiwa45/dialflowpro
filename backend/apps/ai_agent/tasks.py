"""
Celery tasks for the AI Agent app (Phase 2: embeddings wired).

`index_agent_knowledge` chunks every active knowledge item into
AIKnowledgeChunk rows and embeds each chunk via the pluggable provider in
embeddings.py. If the provider is 'none' or fails, chunks are stored without
embeddings and the retriever falls back to lexical matching — so indexing never
hard-fails the agent.
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

_CHUNK_CHARS = 600


def _split(text: str, size: int = _CHUNK_CHARS):
    text = (text or "").strip()
    if len(text) <= size:
        return [text] if text else []
    out, cur, length = [], [], 0
    for sentence in text.replace("\n", " ").split(". "):
        s = sentence.strip()
        if not s:
            continue
        if length + len(s) > size and cur:
            out.append(". ".join(cur) + ".")
            cur, length = [], 0
        cur.append(s)
        length += len(s)
    if cur:
        out.append(". ".join(cur))
    return out


def embed_text(text: str):
    """
    Return an embedding vector for `text`. Delegates to the configured provider.
    Raises NotImplementedError when embeddings are disabled, which callers treat
    as 'use lexical fallback'.
    """
    from .embeddings import embed
    return embed(text)


@shared_task(name="ai_agent.index_agent_knowledge", bind=True, max_retries=2)
def index_agent_knowledge(self, agent_id: int):
    from .models import AIAgent, AIKnowledgeChunk
    from .constants import AIAgentStatus

    try:
        agent = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        logger.error("index_agent_knowledge: agent %s gone", agent_id)
        return

    AIKnowledgeChunk.objects.filter(agent=agent).delete()

    total = 0
    embed_failures = 0
    for item in agent.knowledge_items.filter(is_active=True):
        body = item.content
        if item.source_type == "product" and item.product_name:
            body = f"{item.product_name}. {item.product_price}. {body}"
        for piece in _split(body):
            emb = None
            try:
                emb = embed_text(piece)
            except NotImplementedError:
                emb = None  # embeddings disabled by config
            except Exception as exc:
                embed_failures += 1
                logger.warning("embed failed: %s", exc)
                emb = None
            AIKnowledgeChunk.objects.create(
                agent=agent, item=item, text=piece,
                embedding=emb, token_count=len(piece.split()),
            )
            total += 1

    agent.kb_chunk_count = total
    agent.kb_last_indexed = timezone.now()
    if agent.status == AIAgentStatus.TRAINING:
        agent.status = AIAgentStatus.DRAFT
    agent.save(update_fields=[
        "kb_chunk_count", "kb_last_indexed", "status", "updated_date"
    ])
    logger.info("Indexed %s chunks for AI agent %s (%s embed failures)",
                total, agent_id, embed_failures)
    return total
