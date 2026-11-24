import json
import urllib.parse
from typing import List, Dict, Any
import requests
from app.core.logging import logger
from app.core.config import settings

def search_duckduckgo(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Perform web search using duckduckgo_search library."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("body", ""),
                    "url": item.get("href", "")
                })
        if results:
            return results
    except Exception as e:
        logger.warning(f"duckduckgo_search library search error: {e}. Attempting fallback...")
    return []

def search_wikipedia_fallback(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Fallback search using Wikipedia REST API."""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&utf8=&format=json"
        headers = {"User-Agent": "MultiToolAIAgent/1.0 (test@example.com)"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            search_items = data.get("query", {}).get("search", [])
            results = []
            for item in search_items[:max_results]:
                # Remove basic html tags from snippet
                snippet = item.get("snippet", "").replace('<span class="searchmatch">', "").replace('</span>', "")
                page_id = item.get("pageid")
                page_url = f"https://en.wikipedia.org/?curid={page_id}" if page_id else ""
                results.append({
                    "title": item.get("title", ""),
                    "snippet": snippet,
                    "url": page_url
                })
            return results
    except Exception as e:
        logger.warning(f"Wikipedia fallback search error: {e}")
    return []

def web_search(query: str, max_results: int = 4) -> str:
    """
    Search the web for relevant information regarding a query.
    Returns formatted search results or a clear status message.
    """
    clean_query = query.strip()
    if not clean_query:
        return "Search query cannot be empty."

    logger.info(f"Executing web search for: '{clean_query}' (limit: {max_results})")
    
    # Try primary search (DuckDuckGo)
    results = search_duckduckgo(clean_query, max_results=max_results)
    
    # If no results or error, try Wikipedia fallback
    if not results:
        results = search_wikipedia_fallback(clean_query, max_results=max_results)
        
    if not results:
        return (
            f"No live web results could be retrieved for '{clean_query}'. "
            "Please ensure network access is enabled, or formulate a response based on existing knowledge."
        )

    formatted = []
    for idx, r in enumerate(results, start=1):
        formatted.append(
            f"[{idx}] Title: {r['title']}\n"
            f"    Snippet: {r['snippet']}\n"
            f"    Source: {r['url']}"
        )
    return "\n\n".join(formatted)
