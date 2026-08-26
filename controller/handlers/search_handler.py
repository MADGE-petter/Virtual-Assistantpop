"""Search Handler - Xử lý tìm kiếm."""

import re
import webbrowser
from urllib.parse import quote_plus

from controller.handlers.base_handler import BaseHandler
from service.intern import extract_search_query


class SearchHandler(BaseHandler):
    """Handler for search queries."""
    
    YOUTUBE_PATTERNS = [
        r'\btrên\s+yt\b',
        r'\btrên\s+youtube\b',
        r'\byoutube\b',
        r'\byt\b'
    ]

    def handle(self, text):
        """Xử lý tìm kiếm."""
        search_query = extract_search_query(text)
        if not search_query:
            return "need_search_query"

        text_lower = text.lower()
        is_youtube = any(re.search(pattern, text_lower) for pattern in self.YOUTUBE_PATTERNS)

        if is_youtube:
            webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(search_query)}")
            return f"Tôi đã tìm kiếm {search_query} trên YouTube."

        webbrowser.open(f"https://www.google.com/search?q={quote_plus(search_query)}")
        return f"Tôi đã tìm kiếm {search_query} trên Google."
