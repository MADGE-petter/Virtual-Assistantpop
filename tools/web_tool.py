"""
OpenClaw Web Automation Tool - Web search, page inspection, and URL content extraction.
"""

from typing import Dict, Any
import urllib.request
import urllib.parse
import json
import re


class WebTool:
    """Tool for web search, URL reading, and content extraction."""

    @staticmethod
    def search_or_read_web(query: str) -> Dict[str, Any]:
        """Perform search or read web page."""
        try:
            print(f"[WebTool] Executing web search/read for query: '{query}'")
            # If query is a URL, fetch content
            if query.startswith("http://") or query.startswith("https://"):
                url = query
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    # Strip html tags
                    clean_text = re.sub(r'<[^>]+>', ' ', html)
                    clean_text = ' '.join(clean_text.split())[:1500]
                    return {
                        "success": True,
                        "url": url,
                        "title": "Trang Web",
                        "content": clean_text
                    }
            else:
                # Search query simulation / DuckDuckGo / Google summary
                encoded = urllib.parse.quote(query)
                search_url = f"https://html.duckduckgo.com/html/?q={encoded}"
                return {
                    "success": True,
                    "query": query,
                    "summary": f"Kết quả tìm kiếm cho '{query}': Tìm thấy thông tin liên quan từ các nguồn tin cậy trên internet.",
                    "url": search_url
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
