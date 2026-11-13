from dataclasses import dataclass


@dataclass(frozen=True)
class Visit:
    """Who followed a short url: the data saved as a Click."""

    ip_address: str
    user_agent: str = ""
    referrer: str | None = None
