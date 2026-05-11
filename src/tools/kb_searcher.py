import json
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def search_knowledge_base(query: str, category: str = None, top_k: int = 5) -> dict:
    """
    Search the knowledge base for matching solutions.

    Args:
        query: Search query (issue description)
        category: Optional category filter
        top_k: Number of top results to return

    Returns:
        Dictionary with matching articles
    """
    logger.info(f"Searching KB with query: '{query}'")

    # Load knowledge base
    kb = _load_kb()
    matches = []

    # Search through articles
    for article in kb["articles"]:
        score = _calculate_relevance(query, article, category)
        if score > 0.0:
            article["relevance_score"] = score
            matches.append(article)

    # Sort by relevance and return top_k
    matches.sort(key=lambda x: x["relevance_score"], reverse=True)
    top_matches = matches[:top_k]

    result = {
        "query": query,
        "total_matches": len(matches),
        "top_k_results": top_k,
        "matches": [_format_match(m) for m in top_matches]
    }

    logger.info(f"Found {len(top_matches)} matching articles")
    return result


def _load_kb() -> dict:
    """Load knowledge base from JSON file"""
    try:
        with open("config/kb_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Knowledge base file not found")
        return {"articles": []}


def _calculate_relevance(query: str, article: dict, category_filter: str = None) -> float:
    """Calculate relevance score between query and article"""
    query_lower = query.lower()

    # If category filter provided and doesn't match, return 0
    if category_filter and article.get("category", "").lower() != category_filter.lower():
        return 0.0

    # Score based on keyword matches
    score = 0.0

    # Title match (highest weight)
    title_words = article.get("title", "").lower().split()
    for word in query_lower.split():
        if len(word) > 3:  # Skip small words
            if word in article.get("title", "").lower():
                score += 0.3

    # Keywords match (medium weight)
    article_keywords = article.get("keywords", [])
    for keyword in article_keywords:
        if keyword.lower() in query_lower:
            score += 0.2

    # Solution summary match (low weight)
    summary_words = article.get("solution_summary", "").lower().split()
    query_words = [w for w in query_lower.split() if len(w) > 3]
    for word in query_words:
        if word in summary_words:
            score += 0.1

    # Normalize score to 0-1 range
    score = min(score / 2.0, 1.0)  # Normalize to max 1.0

    return score


def _format_match(article: dict) -> dict:
    """Format article for response"""
    formatted = {
        "article_id": article.get("article_id"),
        "title": article.get("title"),
        "category": article.get("category"),
        "relevance_score": round(article.get("relevance_score", 0), 2),
        "solution_summary": article.get("solution_summary"),
        "steps": article.get("steps", []),
        "prerequisites": article.get("prerequisites"),
    }

    if article.get("source_url"):
        formatted["source_url"] = article.get("source_url")
    if article.get("last_verified_utc"):
        formatted["last_verified_utc"] = article.get("last_verified_utc")
    if article.get("service"):
        formatted["service"] = article.get("service")

    return formatted
