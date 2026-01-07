import hashlib
from typing import Optional, Dict


class URLShortener:
    """
    A simple URL shortener class that generates short URLs with customizable aliases.
    Uses only standard Python libraries.
    """

    def __init__(self):
        self.url_map: Dict[str, str] = {}

    def shorten_url(self, original_url: str, custom_alias: Optional[str] = None) -> str:
        """
        Shortens the given URL with an optional custom alias.

        :param original_url: The original URL to be shortened.
        :param custom_alias: An optional custom alias for the shortened URL.
        :return: The shortened URL.
        :raises ValueError: If the custom alias is already in use.
        """
        if custom_alias:
            if custom_alias in self.url_map:
                raise ValueError("Alias already in use.")
            short_url = custom_alias
        else:
            short_url = hashlib.md5(original_url.encode()).hexdigest()[:6]

        self.url_map[short_url] = original_url
        return short_url

    def resolve_url(self, short_url: str) -> Optional[str]:
        """
        Resolves the shortened URL to the original URL.

        :param short_url: The shortened URL.
        :return: The original URL if found, else None.
        """
        return self.url_map.get(short_url)
    
    def list_all(self) -> Dict[str, str]:
        """Returns all shortened URLs."""
        return self.url_map.copy()


if __name__ == "__main__":
    shortener = URLShortener()

    print("=== URL Shortener Demo ===\n")
    
    # Demo 1: Custom alias
    try:
        url1 = "https://www.example.com/very/long/path/to/page"
        alias1 = "exmpl"
        short1 = shortener.shorten_url(url1, alias1)
        print(f"Original: {url1}")
        print(f"Shortened (custom): {short1}")
        print(f"Resolved: {shortener.resolve_url(short1)}\n")
    except ValueError as e:
        print(f"Error: {e}")

    # Demo 2: Auto-generated alias
    url2 = "https://www.google.com/search?q=python"
    short2 = shortener.shorten_url(url2)
    print(f"Original: {url2}")
    print(f"Shortened (auto): {short2}")
    print(f"Resolved: {shortener.resolve_url(short2)}\n")

    # Demo 3: Duplicate alias error
    try:
        shortener.shorten_url("https://another.com", "exmpl")
    except ValueError as e:
        print(f"Expected error for duplicate alias: {e}\n")

    # List all
    print("All shortened URLs:")
    for short, original in shortener.list_all().items():
        print(f"  {short} -> {original}")
