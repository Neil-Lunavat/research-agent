#!/usr/bin/env python3
"""
Preprocessing utilities for building clean text for embeddings
"""

from typing import Optional


def build_document_for_embedding(title: str, summary: Optional[str], full_content: Optional[str]) -> str:
    parts = []
    title = (title or '').strip()
    if title:
        parts.append(f"Title: {title}")
    summary = (summary or '').strip()
    if summary and summary.lower() != 'unknown':
        parts.append(f"Summary: {summary}")
    content = (full_content or '').strip()
    if content:
        parts.append("Content:\n" + content)
    return "\n\n".join(parts)



