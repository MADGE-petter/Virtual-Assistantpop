"""
OpenClaw File Search Tool - Smart local computer file search by name & content.
"""

import os
from pathlib import Path
from typing import List, Dict, Any


class FileSearchTool:
    """Smart File Search across computer drives."""

    SEARCH_DIRS = [
        str(Path.home() / "Desktop"),
        str(Path.home() / "Documents"),
        str(Path.home() / "Downloads"),
    ]

    @classmethod
    def search_files(cls, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search files matching query in name or content."""
        query_lower = query.lower()
        results = []

        print(f"[FileSearchTool] Searching computer files for query: '{query}'")

        for sdir in cls.SEARCH_DIRS:
            if not os.path.exists(sdir):
                continue
            try:
                for root, _, files in os.walk(sdir):
                    for fname in files:
                        if fname.startswith("~$") or fname.startswith("."):
                            continue
                        fpath = os.path.join(root, fname)

                        # Match filename
                        if query_lower in fname.lower():
                            size_kb = round(os.path.getsize(fpath) / 1024.0, 1)
                            results.append({
                                "name": fname,
                                "path": fpath,
                                "size": f"{size_kb} KB",
                                "extension": os.path.splitext(fname)[1].upper(),
                                "match_type": "Tên tệp"
                            })
                            if len(results) >= max_results:
                                return results
            except Exception as e:
                print(f"[FileSearchTool] Error scanning {sdir}: {e}")

        return results
