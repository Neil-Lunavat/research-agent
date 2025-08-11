#!/usr/bin/env python3
"""
Market validation: combine DB metrics and social signals into a simple score and report.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime

from src.storage.db import DatabaseManager


class MarketValidator:
    def __init__(self):
        pass

    def _compute_score(self, db_metrics: Dict[str, Any], social_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        social_score = sum(item.get('score', 0) + item.get('comments', 0) * 0.5 for item in social_items)
        base_score = (
            db_metrics.get('articles', 0) * 1.0 +
            db_metrics.get('hn_points', 0) * 0.5 +
            db_metrics.get('hn_comments', 0) * 0.2 +
            db_metrics.get('crawled_count', 0) * 0.1
        )
        total = base_score + social_score
        return {
            'base_score': base_score,
            'social_score': social_score,
            'total_score': total
        }

    def generate_report(self, db: DatabaseManager, social_items: List[Dict[str, Any]], topic: str, days: int) -> Tuple[str, Dict[str, Any]]:
        metrics = db.aggregate_signals(topic=topic, days=days)
        scores = self._compute_score(metrics, social_items)

        lines = []
        lines.append(f"# Market Validation Report: {topic}")
        lines.append(f"Generated: {datetime.utcnow().isoformat()} UTC")
        lines.append("")
        lines.append("## Metrics")
        lines.append(f"- Articles collected: {metrics['articles']}")
        lines.append(f"- HN points total: {metrics['hn_points']}")
        lines.append(f"- HN comments total: {metrics['hn_comments']}")
        lines.append(f"- Crawled content count: {metrics['crawled_count']}")
        lines.append("")
        lines.append("## Social Signals (sample)")
        for item in social_items[:10]:
            lines.append(f"- [{item.get('title','')}]({item.get('url','')}) | score={item.get('score',0)} comments={item.get('comments',0)}")
        if not social_items:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Scores")
        lines.append(f"- Base score: {scores['base_score']:.2f}")
        lines.append(f"- Social score: {scores['social_score']:.2f}")
        lines.append(f"- Total score: {scores['total_score']:.2f}")
        lines.append("")
        lines.append("## Notes")
        lines.append("This is a heuristic MVP score combining collection volume and social traction.")

        return "\n".join(lines), {'metrics': metrics, 'scores': scores}



