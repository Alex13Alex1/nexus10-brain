```python
import hashlib
from typing import Optional, Dict

class URLShortener:
    """
    A simple URL shortener class that generates short URLs with customizable aliases.
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

if __name__ == "__main__":
    shortener = URLShortener()

    try:
        original_url = "https://www.example.com"
        custom_alias = "exmpl"
        short_url = shortener.shorten_url(original_url, custom_alias)
        print(f"Shortened URL: {short_url}")

        resolved_url = shortener.resolve_url(short_url)
        print(f"Resolved URL: {resolved_url}")
    except ValueError as e:
        print(f"Error: {e}")
```

This code defines a simple URL shortener class that allows users to shorten URLs with optional custom aliases. It includes error handling for alias collisions and demonstrates usage in the `if __name__ == "__main__"` block. The code uses only standard Python libraries and is ready to run without additional installations.