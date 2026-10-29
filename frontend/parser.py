import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.parts.append(data)

    @property
    def title(self):
        return " ".join(" ".join(self.parts).split()) or None


def is_public_url(url: str) -> bool:
    parsed = urlparse(url)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        return False

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except OSError:
        return False

    return bool(addresses) and all(
        ipaddress.ip_address(address[4][0]).is_global for address in addresses
    )


def fetch_title(url: str) -> str | None:
    current_url = url

    try:
        with httpx.Client(
            timeout=4.0,
            follow_redirects=False,
            headers={"User-Agent": "Keepy/1.0"},
        ) as client:
            for _ in range(6):
                if not is_public_url(current_url):
                    return None

                with client.stream("GET", current_url) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            return None

                        current_url = urljoin(current_url, location)
                        continue

                    response.raise_for_status()

                    if (
                        "text/html"
                        not in response.headers.get("content-type", "").lower()
                    ):
                        return None

                    content = bytearray()

                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > 1_000_000:
                            return None

                    parser = TitleParser()
                    parser.feed(
                        content.decode(
                            response.encoding or "utf-8",
                            errors="replace",
                        )
                    )
                    return parser.title

    except (httpx.HTTPError, OSError, ValueError):
        return None

    return None
