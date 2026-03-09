# Favorites — Design

## Storage
JSON file `data/favorites.json`, keyed by Telegram user_id.
```json
{"123456789": {"drivers": ["VER", "NOR"], "teams": ["mclaren"]}}
```
`FavoritesService` loads on startup, writes atomically on change.

## Bot Commands
- `/favorites` — show current + inline management menu
- `/fav add VER` — quick add driver
- `/fav add team ferrari` — quick add team
- `/fav remove VER` — quick remove
- `/fav clear` — clear all

## Inline Keyboard Flow
- `/favorites` → list + buttons `[➕ Driver]` `[➕ Team]` `[🗑 Clear]`
- `[➕ Driver]` → grid of season drivers (2 per row), ✓ for already-favorited, toggle on tap
- `[➕ Team]` → 10 teams as buttons, ✓ toggle
- `[← Back]` returns to main favorites menu

## Highlight in Results
- Banners (`/race`, `/qualifying`, `/wdc`, `/wcc`): ★ next to favorite driver names
- Standings: visual accent for favorite teams/drivers

## API (WebApp)
- `GET /api/favorites` — current user's favorites
- `POST /api/favorites/drivers/{code}` — toggle driver
- `POST /api/favorites/teams/{slug}` — toggle team

## WebApp
- Settings/profile section with favorite toggles
- Highlight favorites on results/standings pages

## Files to Create/Modify
- NEW: `backend/services/favorites.py`
- NEW: `backend/bot/handlers/favorites.py`
- NEW: `backend/api/routes/favorites.py`
- MODIFY: `backend/bot/handlers/__init__.py` — register favorites handlers
- MODIFY: `backend/bot/app.py` — add /favorites, /fav commands
- MODIFY: `backend/api/router.py` — include favorites router
- MODIFY: `backend/banners/race_result.py` — highlight favorites
- MODIFY: `backend/banners/qualifying_result.py` — highlight favorites
- MODIFY: `backend/banners/standings_banner.py` — highlight favorites
- MODIFY: `backend/i18n/locales/en.yaml` — new keys
- MODIFY: `backend/i18n/locales/ru.yaml` — new keys
- NEW: `webapp/src/pages/FavoritesPage.tsx`
- NEW: `webapp/src/components/favorites/` — toggle components
- MODIFY: `webapp/src/App.tsx` — add route
- MODIFY: `webapp/src/components/layout/BottomNav.tsx` — add tab
