from pathlib import Path

import yaml

_locales: dict[str, dict[str, str]] = {}
_LOCALE_DIR = Path(__file__).parent / "locales"


def _load_locale(lang: str) -> dict[str, str]:
    if lang not in _locales:
        path = _LOCALE_DIR / f"{lang}.yaml"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                _locales[lang] = yaml.safe_load(f) or {}
        else:
            _locales[lang] = {}
    return _locales[lang]


def get_text(key: str, lang: str = "en", **kwargs: object) -> str:
    texts = _load_locale(lang)
    fallback = _load_locale("en")
    template = texts.get(key) or fallback.get(key) or key
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template
