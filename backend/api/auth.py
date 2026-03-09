"""Telegram WebApp initData HMAC-SHA256 validation."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qs, unquote

from fastapi import Header, HTTPException

from backend.config import settings

logger = logging.getLogger(__name__)


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram WebApp initData using HMAC-SHA256.

    Parameters
    ----------
    init_data:
        The raw ``initData`` string from the Telegram WebApp (URL-encoded).
    bot_token:
        The bot token used to derive the secret key.

    Returns
    -------
    dict | None
        Parsed user data if the signature is valid, ``None`` otherwise.
    """
    try:
        # Parse URL-encoded params
        parsed = parse_qs(init_data, keep_blank_values=True)
        # parse_qs returns lists — flatten to single values
        params: dict[str, str] = {k: v[0] for k, v in parsed.items()}

        # Extract and remove the hash
        provided_hash = params.pop("hash", None)
        if not provided_hash:
            logger.debug("No hash found in initData")
            return None

        # Build data-check-string: alphabetically sorted key=value, newline separated
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items())
        )

        # secret_key = HMAC-SHA256("WebAppData", bot_token)
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
        ).digest()

        # computed_hash = HMAC-SHA256(secret_key, data_check_string)
        computed_hash = hmac.new(
            secret_key, data_check_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, provided_hash):
            logger.debug("initData hash mismatch")
            return None

        # Parse the user JSON from the params
        user_raw = params.get("user")
        if user_raw:
            return json.loads(unquote(user_raw))

        # Return all params if no user field
        return params

    except Exception:
        logger.exception("Failed to validate initData")
        return None


async def get_telegram_user(
    authorization: str = Header(default=""),
) -> dict | None:
    """FastAPI dependency that validates Telegram initData from the Authorization header.

    During development this dependency is lenient: if no header is provided
    or validation fails, it returns ``None`` instead of raising an error.
    For production, change the behaviour to raise ``HTTPException(401)``.
    """
    if not authorization:
        return None

    # Strip "tma " or "Bearer " prefix if present
    token = authorization
    for prefix in ("tma ", "Bearer ", "tma+", "Tma "):
        if authorization.startswith(prefix):
            token = authorization[len(prefix):]
            break

    user = validate_init_data(token, settings.telegram_bot_token)
    if user is None:
        logger.debug("Invalid or missing Telegram initData")
        # Lenient during dev — return None instead of 401
        return None

    return user
