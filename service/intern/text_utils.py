"""Text extraction utilities - Shared text processing functions."""
import re
from typing import Optional


def extract_name(text: str) -> Optional[str]:
    """Extract person name from text."""
    if not text:
        return None
    
    patterns = [
        r'tên là\s+(\w+)',
        r'tôi là\s+(\w+)',
        r'mình là\s+(\w+)',
        r'gọi tôi là\s+(\w+)',
        r'(\w+)\s+đây',
        r'tôi tên\s+(\w+)',
        r'mình tên\s+(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_domain(text: str) -> Optional[str]:
    """Extract domain/URL from text."""
    if not text:
        return None
    
    # Common domain mappings
    domain_mappings = {
        "google": "google.com",
        "youtube": "youtube.com",
        "facebook": "facebook.com",
        "gmail": "gmail.com",
        "github": "github.com",
    }
    
    text_lower = text.lower().strip()
    
    # Try explicit domain extraction with "mở" or "truy cập"
    domain_match = re.search(
        r"(?:mở|truy cập)\s+(?:trang web)?\s*(\S+)",
        text, re.IGNORECASE
    )
    if domain_match:
        domain = domain_match.group(1).strip().lower()
        
        if domain in domain_mappings:
            domain = domain_mappings[domain]
        
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        
        return domain
    
    # Fallback: nếu text chỉ chứa tên website (vd: "youtube", "google")
    for name, url in domain_mappings.items():
        if name in text_lower:
            return f"https://{url}"
    
    return None


def extract_app_name(text: str) -> Optional[str]:
    """Extract application name from text."""
    if not text:
        return None
    
    text_lower = text.lower().strip()
    open_keywords = [
        "mở app", "mở ứng dụng", "mở chương trình",
        "chạy app", "khởi động app", "bật app",
        "mở", "chạy", "khởi động", "bật"
    ]
    
    # Remove opening keywords
    app_name = text_lower
    for keyword in open_keywords:
        if app_name.startswith(keyword + " "):
            app_name = app_name[len(keyword):].strip()
            break
    
    # Remove filler words
    filler_words = ["ra", "lên", "giúp tôi", "đi", "nhanh"]
    for word in filler_words:
        if app_name.startswith(word + " "):
            app_name = app_name[len(word):].strip()
    
    return app_name if app_name else None


def extract_file_reference(text: str) -> Optional[str]:
    """Extract file reference from text."""
    if not text:
        return None
    
    patterns = [
        r'file\s+(\S+)',
        r'tệp\s+(\S+)',
        r'document\s+(\S+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_location(text: str) -> Optional[str]:
    """Extract location/city name from text.
    
    Simple approach: if short text (<=3 words), likely a location name.
    Returns location string or None.
    """
    if not text:
        return None
    
    # Strip common prefixes
    cleaned = text.strip()
    prefixes = ['ở ', 'tại ', 'tại']
    for prefix in prefixes:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    
    # Simple heuristic: short text = likely location
    words = cleaned.split()
    if len(words) <= 3 and len(cleaned) > 1:
        return cleaned
    
    return None


def extract_search_query(text: str) -> Optional[str]:
    """Extract search query from text."""
    if not text:
        return None
    
    patterns = [
        r"(?:tìm kiếm|tra cứu|tìm trên google|search google|tìm kiếm trên google)\s+(.+)",
        r"(?:tôi muốn tìm|tìm giúp tôi)\s+(.+)",
        r"(?:tìm|search)\s+(.+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            search_query = match.group(1).strip()
            # Remove command words and search service qualifiers
            search_query = re.sub(
                r'\b(tìm kiếm|tra cứu|tìm trên google|search google|tìm kiếm trên google|tôi muốn tìm|tìm giúp tôi|tìm|search|trên yt|trên youtube|trên web|trên trang web|trên google)\b',
                '', search_query, flags=re.IGNORECASE
            )
            search_query = re.sub(r'\s+', ' ', search_query).strip()
            return search_query
    
    return None
