import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
CACHE_DIRECTORY = PROJECT_ROOT / ".cache"
CACHE_FILENAME = "history.json"


def get_cache_path(cache_directory=CACHE_DIRECTORY, cache_filename=CACHE_FILENAME):
    return Path(cache_directory) / cache_filename


def get_gacha_cache_path(cache_key, cache_directory=CACHE_DIRECTORY):
    game, banner = cache_key.split(":", 1)
    return Path(cache_directory) / game / banner / CACHE_FILENAME


def load_history_cache():
    cache = {}
    for cache_path in CACHE_DIRECTORY.glob("*/*/history.json"):
        game, banner, _ = cache_path.relative_to(CACHE_DIRECTORY).parts
        with cache_path.open("r", encoding="utf-8") as cache_file:
            pulls = json.load(cache_file)
        if not isinstance(pulls, list):
            raise ValueError(f"History cache must contain a list: {cache_path}")
        cache[f"{game}:{banner}"] = pulls

    legacy_cache_path = get_cache_path()
    if legacy_cache_path.exists():
        with legacy_cache_path.open("r", encoding="utf-8") as cache_file:
            legacy_cache = json.load(cache_file)
        if not isinstance(legacy_cache, dict):
            raise ValueError("Legacy history cache must contain an object.")
        for cache_key, pulls in legacy_cache.items():
            cache.setdefault(cache_key, pulls)
    return cache


def _pull_key(pull):
    if pull.get("id") is not None:
        return f"id:{pull['id']}"
    return "|".join(
        str(pull.get(field, ""))
        for field in ("time", "name", "item_type", "rank_type")
    )


def _normalize_pull(pull):
    normalized_pull = dict(pull)
    if normalized_pull.get("item_type") == "Karakter":
        normalized_pull["item_type"] = "Character"
    return normalized_pull


def merge_pull_history(existing_pulls, new_pulls):
    pulls_by_key = {}
    for pull in [*existing_pulls, *new_pulls]:
        pull = _normalize_pull(pull)
        pulls_by_key[_pull_key(pull)] = pull
    return sorted(
        pulls_by_key.values(),
        key=lambda pull: (pull.get("time", ""), str(pull.get("id", ""))),
        reverse=True,
    )


def save_history_cache(cache):
    for cache_key, pulls in cache.items():
        cache_path = get_gacha_cache_path(cache_key)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = cache_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as cache_file:
            json.dump(pulls, cache_file, ensure_ascii=True, indent=2)
        temporary_path.replace(cache_path)
