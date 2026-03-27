"""Auto-extract session tokens from the user's installed browsers."""

from typing import Optional

import browser_cookie3


PROVIDER_COOKIES = {
    "anthropic": {
        "domain": "claude.ai",
        "cookie_name": "sessionKey",
    },
    "openai": {
        "domain": "chatgpt.com",
        "cookie_name": "__Secure-next-auth.session-token",
    },
}

# Browsers to try, in order of popularity on Windows
_BROWSERS = [
    ("Chrome", browser_cookie3.chrome),
    ("Edge", browser_cookie3.edge),
    ("Firefox", browser_cookie3.firefox),
]


def extract_token(provider_key: str) -> tuple[Optional[str], Optional[str]]:
    """Try to auto-extract a session token from installed browsers.

    Returns (token, browser_name) on success, or (None, error_message) on failure.
    """
    info = PROVIDER_COOKIES.get(provider_key)
    if info is None:
        return None, f"Unknown provider: {provider_key}"

    domain = info["domain"]
    cookie_name = info["cookie_name"]
    errors = []

    for browser_name, cookie_fn in _BROWSERS:
        try:
            cj = cookie_fn(domain_name=f".{domain}")
            for cookie in cj:
                if cookie.name == cookie_name and domain in cookie.domain:
                    return cookie.value, browser_name
        except PermissionError:
            errors.append(f"{browser_name}: permission denied (try closing the browser first)")
        except Exception as exc:
            errors.append(f"{browser_name}: {exc}")

    if errors:
        detail = "\n".join(errors)
        return None, (
            f"Could not find {domain} session token.\n\n"
            f"Make sure you are logged in to {domain} in your browser.\n\n"
            f"Details:\n{detail}"
        )

    return None, (
        "No supported browser found.\n"
        "Install Chrome, Edge, or Firefox and log in to "
        f"{domain}, then try again."
    )
