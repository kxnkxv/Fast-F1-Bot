"""Favorites service — persistent storage of user favorite drivers and teams."""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_PATH = Path("data/favorites.json")


class UserFavorites:
    """Favorites for a single user."""

    __slots__ = ("drivers", "teams")

    def __init__(self, drivers: list[str] | None = None, teams: list[str] | None = None):
        self.drivers: list[str] = drivers or []
        self.teams: list[str] = teams or []

    def to_dict(self) -> dict[str, list[str]]:
        return {"drivers": self.drivers, "teams": self.teams}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserFavorites:
        return cls(
            drivers=list(data.get("drivers", [])),
            teams=list(data.get("teams", [])),
        )

    def is_empty(self) -> bool:
        return not self.drivers and not self.teams

    def has_driver(self, code: str) -> bool:
        return code.upper() in self.drivers

    def has_team(self, slug: str) -> bool:
        return slug.lower() in self.teams

    def toggle_driver(self, code: str) -> bool:
        """Toggle driver favorite. Returns True if added, False if removed."""
        code = code.upper()
        if code in self.drivers:
            self.drivers.remove(code)
            return False
        self.drivers.append(code)
        return True

    def toggle_team(self, slug: str) -> bool:
        """Toggle team favorite. Returns True if added, False if removed."""
        slug = slug.lower()
        if slug in self.teams:
            self.teams.remove(slug)
            return False
        self.teams.append(slug)
        return True

    def clear(self) -> None:
        self.drivers.clear()
        self.teams.clear()


class FavoritesService:
    """Manages user favorites with JSON file persistence."""

    def __init__(self, path: Path = _DEFAULT_PATH):
        self._path = path
        self._data: dict[str, UserFavorites] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            logger.info("No favorites file found at %s, starting fresh", self._path)
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                raw = json.load(f)
            for uid, fav_data in raw.items():
                self._data[str(uid)] = UserFavorites.from_dict(fav_data)
            logger.info("Loaded favorites for %d users", len(self._data))
        except Exception:
            logger.exception("Failed to load favorites from %s", self._path)

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_suffix(".tmp")
            payload = {uid: fav.to_dict() for uid, fav in self._data.items()}
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self._path)
        except Exception:
            logger.exception("Failed to save favorites to %s", self._path)

    def get(self, user_id: int) -> UserFavorites:
        key = str(user_id)
        if key not in self._data:
            self._data[key] = UserFavorites()
        return self._data[key]

    def toggle_driver(self, user_id: int, code: str) -> bool:
        with self._lock:
            result = self.get(user_id).toggle_driver(code)
            self._save()
            return result

    def toggle_team(self, user_id: int, slug: str) -> bool:
        with self._lock:
            result = self.get(user_id).toggle_team(slug)
            self._save()
            return result

    def clear(self, user_id: int) -> None:
        with self._lock:
            self.get(user_id).clear()
            self._save()

    def is_favorite_driver(self, user_id: int, code: str) -> bool:
        return self.get(user_id).has_driver(code)

    def is_favorite_team(self, user_id: int, slug: str) -> bool:
        return self.get(user_id).has_team(slug)


# Global instance
favorites_service = FavoritesService()
