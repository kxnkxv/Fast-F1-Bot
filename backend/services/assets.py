"""F1 CDN asset loader — fetches and caches driver photos, team cars, logos, etc."""

from __future__ import annotations

import logging

import httpx

from backend.cache.manager import TTL_ASSETS, cache
from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CDN URL templates
# ---------------------------------------------------------------------------
F1_CDN = "https://media.formula1.com/image/upload"

DRIVER_PHOTO = (
    "{cdn}/c_lfill,w_{size}/q_auto/"
    "d_common:f1:{year}:fallback:driver:{year}fallbackdriverright.webp/"
    "v1/common/f1/{year}/{team}/{driver_code}/{year}{team}{driver_code}right.webp"
)

DRIVER_NUMBER = (
    "{cdn}/c_fit,w_876,h_742/q_auto/"
    "v1/common/f1/{year}/{team}/{driver_code}/{year}{team}{driver_code}numberwhitefrless.webp"
)

TEAM_CAR = (
    "{cdn}/c_lfill,h_{size}/q_auto/"
    "d_common:f1:{year}:fallback:car:{year}fallbackcarright.webp/"
    "v1/common/f1/{year}/{team}/{year}{team}carright.webp"
)

TEAM_LOGO = (
    "{cdn}/c_lfill,w_{size}/q_auto/"
    "v1/common/f1/{year}/{team}/{year}{team}logowhite.webp"
)

RACE_CARD = (
    "{cdn}/c_lfill,w_{size}/q_auto/"
    "v1/fom-website/static-assets/{year}/races/card/{country}.webp"
)

# Default image sizes
DEFAULT_DRIVER_PHOTO_WIDTH = 600
DEFAULT_CAR_HEIGHT = 400
DEFAULT_LOGO_WIDTH = 400
DEFAULT_RACE_CARD_WIDTH = 800

# HTTP timeout for CDN requests
_HTTP_TIMEOUT = 15.0


class F1AssetService:
    """Fetches and caches binary assets from the F1 CDN."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create a shared ``httpx.AsyncClient``."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(_HTTP_TIMEOUT),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def get_driver_photo(
        self,
        year: int,
        team_slug: str,
        driver_code: str,
        size: int = DEFAULT_DRIVER_PHOTO_WIDTH,
    ) -> bytes:
        """Fetch the driver headshot photo."""
        url = DRIVER_PHOTO.format(
            cdn=F1_CDN,
            year=year,
            team=team_slug,
            driver_code=driver_code,
            size=size,
        )
        cache_key = cache.make_key("asset", "driver_photo", year, team_slug, driver_code, size)
        return await self._fetch_cached(cache_key, url)

    async def get_driver_number(
        self,
        year: int,
        team_slug: str,
        driver_code: str,
    ) -> bytes:
        """Fetch the driver number graphic."""
        url = DRIVER_NUMBER.format(
            cdn=F1_CDN,
            year=year,
            team=team_slug,
            driver_code=driver_code,
        )
        cache_key = cache.make_key("asset", "driver_number", year, team_slug, driver_code)
        return await self._fetch_cached(cache_key, url)

    async def get_team_car(
        self,
        year: int,
        team_slug: str,
        size: int = DEFAULT_CAR_HEIGHT,
    ) -> bytes:
        """Fetch the team car image."""
        url = TEAM_CAR.format(
            cdn=F1_CDN,
            year=year,
            team=team_slug,
            size=size,
        )
        cache_key = cache.make_key("asset", "team_car", year, team_slug, size)
        return await self._fetch_cached(cache_key, url)

    async def get_team_logo(
        self,
        year: int,
        team_slug: str,
        size: int = DEFAULT_LOGO_WIDTH,
    ) -> bytes:
        """Fetch the team logo."""
        url = TEAM_LOGO.format(
            cdn=F1_CDN,
            year=year,
            team=team_slug,
            size=size,
        )
        cache_key = cache.make_key("asset", "team_logo", year, team_slug, size)
        return await self._fetch_cached(cache_key, url)

    async def get_race_card(
        self,
        year: int,
        country: str,
        size: int = DEFAULT_RACE_CARD_WIDTH,
    ) -> bytes:
        """Fetch the race weekend card image."""
        url = RACE_CARD.format(
            cdn=F1_CDN,
            year=year,
            country=country,
            size=size,
        )
        cache_key = cache.make_key("asset", "race_card", year, country, size)
        return await self._fetch_cached(cache_key, url)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    async def _fetch_cached(self, cache_key: str, url: str) -> bytes:
        """Return cached bytes or fetch from the CDN and cache the result."""
        # Check Redis binary cache first
        cached = await cache.get_bytes(cache_key)
        if cached is not None:
            logger.debug("Asset cache hit: %s", cache_key)
            return cached

        data = await self._download(url)
        if data:
            await cache.set_bytes(cache_key, data, ttl=TTL_ASSETS)
        return data

    async def _download(self, url: str) -> bytes:
        """Download binary content from a URL."""
        client = await self._get_client()
        try:
            response = await client.get(url)
            response.raise_for_status()
            logger.debug("Downloaded asset: %s (%d bytes)", url, len(response.content))
            return response.content
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "CDN returned %d for %s",
                exc.response.status_code,
                url,
            )
            return b""
        except httpx.RequestError as exc:
            logger.error("CDN request failed for %s: %s", url, exc)
            return b""


# Global instance
asset_service = F1AssetService()
