"""OpenAI / ChatGPT usage provider."""

import time
from datetime import datetime, timedelta, timezone

import requests

from .. import http_client
from .base import ProviderUsage, UsageProvider, UsageTier


class OpenAIProvider(UsageProvider):
    name = "OpenAI (ChatGPT)"

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

    # ── session-token path (ChatGPT consumer) ──────────────────────

    def _fetch_via_session(self, session_token: str) -> ProviderUsage:
        headers = {
            "Authorization": f"Bearer {session_token}",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
                "Gecko/20100101 Firefox/115.0"
            ),
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://chatgpt.com/",
            "Origin": "https://chatgpt.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive",
        }

        resp = http_client.get(
            "https://chatgpt.com/backend-api/accounts/check/v4-2023-04-27",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        return self._parse_session_data(data)

    # ── api-key path (OpenAI API users) ─────────────────────────────

    def _fetch_via_api_key(self, api_key: str) -> ProviderUsage:
        headers = {"Authorization": f"Bearer {api_key}"}
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = start_of_day - timedelta(days=now.weekday())
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        tiers = []

        # Fetch costs for the current billing period
        try:
            costs_resp = requests.get(
                "https://api.openai.com/v1/organization/costs",
                headers=headers,
                params={
                    "start_time": int(start_of_month.timestamp()),
                    "end_time": int(now.timestamp()),
                    "bucket_width": "1d",
                },
                timeout=15,
            )
            if costs_resp.status_code == 200:
                costs_data = costs_resp.json()
                tiers.extend(self._parse_costs(costs_data, now, start_of_day, start_of_week))
        except requests.RequestException:
            pass

        # Fetch completions usage for daily breakdown
        try:
            usage_resp = requests.get(
                "https://api.openai.com/v1/organization/usage/completions",
                headers=headers,
                params={
                    "start_time": int(start_of_day.timestamp()),
                    "end_time": int(now.timestamp()),
                    "bucket_width": "1d",
                },
                timeout=15,
            )
            if usage_resp.status_code == 200:
                usage_data = usage_resp.json()
                tiers.extend(self._parse_completions(usage_data))
        except requests.RequestException:
            pass

        if not tiers:
            # Fallback: try the older billing endpoint
            tiers = self._fetch_legacy_billing(headers, now)

        if not tiers:
            tiers.append(UsageTier(
                label="API Status",
                used_percent=0,
                detail="Connected – no usage data available yet",
            ))

        return ProviderUsage(provider_name=self.name, tiers=tiers)

    # ── parsers ──────────────────────────────────────────────────────

    def _parse_session_data(self, data: dict) -> ProviderUsage:
        """Parse chatgpt.com accounts/check response."""
        tiers = []

        accounts = data.get("accounts", {})
        for acct_id, acct in accounts.items():
            entitlement = acct.get("entitlement", {})
            rate_limits = entitlement.get("rate_limits", [])

            for rl in rate_limits:
                limit = rl.get("limit", 0)
                remaining = rl.get("remaining", limit)
                window = rl.get("window", "")
                reset_seconds = rl.get("reset_seconds", 0)

                if limit <= 0:
                    continue

                used = limit - remaining
                pct = used / limit * 100

                # Determine tier label from window
                if "session" in window.lower() or reset_seconds <= 3600:
                    label = "Current Session"
                elif reset_seconds <= 86400:
                    label = "Daily Usage"
                else:
                    label = "Weekly Usage"

                reset_dt = None
                if reset_seconds > 0:
                    reset_dt = datetime.now(timezone.utc) + timedelta(seconds=reset_seconds)

                tiers.append(UsageTier(
                    label=label,
                    used_percent=pct,
                    reset_at=reset_dt,
                    detail=f"{used} / {limit} messages",
                ))

            # Also check subscription info
            plan = acct.get("entitlement", {}).get("subscription_plan", "")
            if plan and not tiers:
                tiers.append(UsageTier(
                    label="Plan",
                    used_percent=0,
                    detail=plan,
                ))

        if not tiers:
            # Try to extract any usage info from the raw data
            tiers.append(UsageTier(
                label="Status",
                used_percent=0,
                detail="Connected – usage limits not available in response",
            ))

        return ProviderUsage(provider_name=self.name, tiers=tiers)

    def _parse_costs(
        self, data: dict, now: datetime, start_of_day: datetime, start_of_week: datetime
    ) -> list[UsageTier]:
        tiers = []
        buckets = data.get("data", [])

        daily_cost = 0.0
        weekly_cost = 0.0
        monthly_cost = 0.0

        for bucket in buckets:
            ts = bucket.get("start_time", 0)
            amount = sum(
                r.get("amount", {}).get("value", 0)
                for r in bucket.get("results", [])
            )
            bucket_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            monthly_cost += amount
            if bucket_dt >= start_of_week:
                weekly_cost += amount
            if bucket_dt >= start_of_day:
                daily_cost += amount

        # We don't know the hard limit, so show absolute costs
        if monthly_cost > 0 or daily_cost > 0:
            tiers.append(UsageTier(
                label="Daily Cost",
                used_percent=min(daily_cost / max(monthly_cost, 1) * 100, 100),
                detail=f"${daily_cost:.2f} today",
            ))
            tiers.append(UsageTier(
                label="Weekly Cost",
                used_percent=min(weekly_cost / max(monthly_cost, 1) * 100, 100),
                detail=f"${weekly_cost:.2f} this week",
            ))
            tiers.append(UsageTier(
                label="Monthly Cost",
                used_percent=50,  # no hard cap, show midpoint
                detail=f"${monthly_cost:.2f} this month",
            ))

        return tiers

    def _parse_completions(self, data: dict) -> list[UsageTier]:
        tiers = []
        buckets = data.get("data", [])

        total_input = 0
        total_output = 0
        for bucket in buckets:
            for result in bucket.get("results", []):
                total_input += result.get("input_tokens", 0)
                total_output += result.get("output_tokens", 0)

        if total_input > 0 or total_output > 0:
            tiers.append(UsageTier(
                label="Today's Tokens",
                used_percent=0,
                detail=f"{self._fmt(total_input)} in / {self._fmt(total_output)} out",
            ))

        return tiers

    def _fetch_legacy_billing(self, headers: dict, now: datetime) -> list[UsageTier]:
        """Fallback to the older /dashboard/billing endpoint."""
        tiers = []
        try:
            start = now.strftime("%Y-%m-01")
            end = now.strftime("%Y-%m-%d")
            resp = requests.get(
                "https://api.openai.com/dashboard/billing/usage",
                headers=headers,
                params={"start_date": start, "end_date": end},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                total = data.get("total_usage", 0) / 100  # cents to dollars
                tiers.append(UsageTier(
                    label="Monthly Usage",
                    used_percent=50,
                    detail=f"${total:.2f} this month",
                ))
        except requests.RequestException:
            pass
        return tiers

    @staticmethod
    def _fmt(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K"
        return str(n)
