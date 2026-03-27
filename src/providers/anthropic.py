"""Anthropic / Claude usage provider."""

import time
from datetime import datetime, timedelta, timezone

import requests

from .base import ProviderUsage, UsageProvider, UsageTier


def _browser_headers(cookie: str) -> dict:
    """Headers that mimic a real browser session on claude.ai."""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
            "Gecko/20100101 Firefox/115.0"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Referer": "https://claude.ai/chats",
        "Origin": "https://claude.ai",
        "Cookie": cookie,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Connection": "keep-alive",
        "DNT": "1",
    }


class AnthropicProvider(UsageProvider):
    name = "Anthropic (Claude)"

    # ── public interface ────────────────────────────────────────────

    def fetch_usage(self, auth_type: str, credential: str) -> ProviderUsage:
        try:
            if auth_type == "session_token":
                return self._fetch_via_session(credential)
            else:
                return self._fetch_via_api_key(credential)
        except Exception as exc:
            return ProviderUsage(
                provider_name=self.name,
                error=f"Failed to fetch: {exc}",
            )

    # ── session-token path (claude.ai consumer) ────────────────────

    def _fetch_via_session(self, session_key: str) -> ProviderUsage:
        # Build cookie string – if user pasted just the value, wrap it
        if session_key.startswith("sk-ant-"):
            cookie = f"sessionKey={session_key}"
        elif "sessionKey=" in session_key:
            cookie = session_key  # User pasted the full cookie header
        else:
            cookie = f"sessionKey={session_key}"

        headers = _browser_headers(cookie)

        # Step 1: get org id
        org_resp = requests.get(
            "https://claude.ai/api/organizations",
            headers=headers,
            timeout=15,
        )
        org_resp.raise_for_status()
        orgs = org_resp.json()
        if not orgs:
            return ProviderUsage(provider_name=self.name, error="No organizations found")
        org_id = orgs[0].get("uuid") or orgs[0].get("id")

        # Step 2: fetch usage / rate-limit info
        usage_resp = requests.get(
            f"https://claude.ai/api/organizations/{org_id}/usage",
            headers=headers,
            timeout=15,
        )
        usage_resp.raise_for_status()
        data = usage_resp.json()

        return self._parse_usage_data(data)

    # ── api-key path (Anthropic API users) ──────────────────────────

    def _fetch_via_api_key(self, api_key: str) -> ProviderUsage:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # Use a lightweight messages call to read rate-limit headers
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            },
            timeout=15,
        )

        tiers = []

        # Parse rate-limit headers (requests remaining / limit)
        rl_remaining = resp.headers.get("anthropic-ratelimit-requests-remaining")
        rl_limit = resp.headers.get("anthropic-ratelimit-requests-limit")
        rl_reset = resp.headers.get("anthropic-ratelimit-requests-reset")

        if rl_remaining is not None and rl_limit is not None:
            remaining = int(rl_remaining)
            limit = int(rl_limit)
            used = limit - remaining
            pct = (used / limit * 100) if limit > 0 else 0
            reset_dt = None
            if rl_reset:
                try:
                    reset_dt = datetime.fromisoformat(rl_reset.replace("Z", "+00:00"))
                except ValueError:
                    pass
            tiers.append(UsageTier(
                label="Request Rate Limit",
                used_percent=pct,
                reset_at=reset_dt,
                detail=f"{used} / {limit} requests used",
            ))

        # Token rate limits
        tk_remaining = resp.headers.get("anthropic-ratelimit-tokens-remaining")
        tk_limit = resp.headers.get("anthropic-ratelimit-tokens-limit")
        tk_reset = resp.headers.get("anthropic-ratelimit-tokens-reset")

        if tk_remaining is not None and tk_limit is not None:
            remaining = int(tk_remaining)
            limit = int(tk_limit)
            used = limit - remaining
            pct = (used / limit * 100) if limit > 0 else 0
            reset_dt = None
            if tk_reset:
                try:
                    reset_dt = datetime.fromisoformat(tk_reset.replace("Z", "+00:00"))
                except ValueError:
                    pass
            tiers.append(UsageTier(
                label="Token Rate Limit",
                used_percent=pct,
                reset_at=reset_dt,
                detail=f"{self._format_tokens(used)} / {self._format_tokens(limit)} tokens",
            ))

        if not tiers:
            tiers.append(UsageTier(
                label="API Status",
                used_percent=0,
                detail="Connected – rate-limit headers not available",
            ))

        return ProviderUsage(provider_name=self.name, tiers=tiers)

    # ── helpers ──────────────────────────────────────────────────────

    def _parse_usage_data(self, data: dict) -> ProviderUsage:
        """Parse the claude.ai usage endpoint response."""
        tiers = []
        now = datetime.now(timezone.utc)

        # The claude.ai usage endpoint may return different structures.
        # We handle the common patterns.

        # Pattern: daily message limit
        if "daily_usage" in data or "messageLimit" in data:
            msg_used = data.get("messagesUsed", data.get("daily_usage", {}).get("used", 0))
            msg_limit = data.get("messageLimit", data.get("daily_usage", {}).get("limit", 0))
            if msg_limit > 0:
                pct = msg_used / msg_limit * 100
                reset_time = data.get("resetTime") or data.get("daily_usage", {}).get("reset_at")
                reset_dt = None
                if reset_time:
                    try:
                        reset_dt = datetime.fromisoformat(str(reset_time).replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass
                tiers.append(UsageTier(
                    label="Daily Usage",
                    used_percent=pct,
                    reset_at=reset_dt,
                    detail=f"{msg_used} / {msg_limit} messages",
                ))

        # Pattern: has explicit tiers
        for tier_data in data.get("tiers", data.get("limits", [])):
            label = tier_data.get("label", tier_data.get("name", "Usage"))
            used = tier_data.get("used", 0)
            limit = tier_data.get("limit", 0)
            pct = (used / limit * 100) if limit > 0 else 0
            reset_raw = tier_data.get("reset_at") or tier_data.get("resetsAt")
            reset_dt = None
            if reset_raw:
                try:
                    reset_dt = datetime.fromisoformat(str(reset_raw).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
            tiers.append(UsageTier(
                label=label,
                used_percent=pct,
                reset_at=reset_dt,
                detail=f"{used} / {limit}",
            ))

        if not tiers:
            # Fallback: show raw data summary
            tiers.append(UsageTier(
                label="Usage",
                used_percent=0,
                detail="Connected – parsing usage data",
            ))

        return ProviderUsage(provider_name=self.name, tiers=tiers)

    @staticmethod
    def _format_tokens(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K"
        return str(n)
