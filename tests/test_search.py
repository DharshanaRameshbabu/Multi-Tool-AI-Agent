import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.tools.search import web_search

def test_web_search_with_query():
    result = web_search("Retrieval-Augmented Generation", max_results=2)
    assert isinstance(result, str)
    assert len(result) > 0

def test_web_search_empty_query():
    result = web_search("   ")
    assert "cannot be empty" in result.lower()
