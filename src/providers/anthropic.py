"""Anthropic / Claude usage provider."""

import time
from datetime import datetime, timedelta, timezone

import requests

from .. import http_client
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

        # Step 1: get org id (uses curl_cffi to bypass TLS fingerprinting)
        org_resp = http_client.get(
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
        usage_resp = http_client.get(
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

    # Maps API keys → human-readable labels
    _TIER_LABELS = {
        "five_hour": "Current Session (5h)",
        "seven_day": "Weekly Usage",
        "seven_day_opus": "Weekly Opus",
        "seven_day_sonnet": "Weekly Sonnet",
        "seven_day_cowork": "Weekly Cowork",
        "iguana_necktie": "Extended Thinking",
    }

    def _parse_usage_data(self, data: dict) -> ProviderUsage:
        """Parse the claude.ai /usage endpoint response.

        Actual response shape (as of 2026-03):
        {
          "five_hour":        {"utilization": 2.0, "resets_at": "..."},
          "seven_day":        {"utilization": 3.0, "resets_at": "..."},
          "seven_day_sonnet": {"utilization": 0.0, "resets_at": "..."},
          "seven_day_opus":   null,
          "extra_usage":      {"is_enabled": false, ...},
          ...
        }
        `utilization` is a 0-100 percentage.
        """
        tiers = []

        for key, label in self._TIER_LABELS.items():
            tier_data = data.get(key)
            if tier_data is None:
                continue

            pct = tier_data.get("utilization", 0.0)
            reset_raw = tier_data.get("resets_at")
            reset_dt = None
            if reset_raw:
                try:
                    reset_dt = datetime.fromisoformat(
                        str(reset_raw).replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            tiers.append(UsageTier(
                label=label,
                used_percent=pct,
                reset_at=reset_dt,
                detail=f"{pct:.0f}% used",
            ))

        # Extra / overage usage
        extra = data.get("extra_usage")
        if extra and extra.get("is_enabled"):
            used = extra.get("used_credits") or 0
            limit = extra.get("monthly_limit") or 0
            pct = extra.get("utilization") or 0.0
            detail = f"${used:.2f}"
            if limit:
                detail += f" / ${limit:.2f}"
            tiers.append(UsageTier(
                label="Extra Usage Credits",
                used_percent=pct,
                detail=detail,
            ))

        if not tiers:
            tiers.append(UsageTier(
                label="Usage",
                used_percent=0,
                detail="Connected – no usage tiers found",
            ))

        return ProviderUsage(provider_name=self.name, tiers=tiers)

    @staticmethod
    def _format_tokens(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K"
        return str(n)
