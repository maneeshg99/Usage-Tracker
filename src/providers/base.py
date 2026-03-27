"""Abstract base for LLM usage providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UsageTier:
    """A single usage limit tier (session, daily, or weekly)."""
    label: str
    used_percent: float  # 0.0 – 100.0
    reset_at: datetime | None = None  # When this tier resets
    detail: str = ""  # Optional extra info, e.g. "45 / 80 messages"


@dataclass
class ProviderUsage:
    """Aggregated usage data returned by a provider."""
    provider_name: str
    tiers: list[UsageTier] = field(default_factory=list)
    error: str | None = None  # Set if the fetch failed


class UsageProvider(ABC):
    """Interface that each LLM provider must implement."""

    name: str = ""

    @abstractmethod
    def fetch_usage(self, auth_type: str, credential: str) -> ProviderUsage:
        """Fetch current usage data. Must not raise – return error in ProviderUsage."""
        ...
