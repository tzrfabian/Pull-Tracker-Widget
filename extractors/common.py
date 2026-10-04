import os
import re
import urllib.parse


def _source_paths(cache_path):
    user_profile = os.environ.get("USERPROFILE", "")
    full_cache_path = os.path.join(user_profile, cache_path)
    game_root = full_cache_path
    for _ in range(5):
        game_root = os.path.dirname(game_root)
    return [full_cache_path, os.path.join(game_root, "Player.log")]


def _get_query_params(data, gacha_type=None):
    urls = re.findall(rb"https://[^\s\"']+\?[^\s\"']+", data)
    for url_bytes in reversed(urls):
        url = url_bytes.decode("utf-8", errors="ignore")
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        if gacha_type is None or params.get("default_gacha_type", [None])[-1] == str(gacha_type):
            return {key: values[-1] for key, values in params.items()}
    return {}


def get_history_params_from_url(history_url, gacha_type=None):
    parsed_url = urllib.parse.urlsplit(history_url.strip())
    params = urllib.parse.parse_qs(parsed_url.query)
    flattened = {key: values[-1] for key, values in params.items()}
    if not flattened.get("authkey"):
        return {}
    if (
        gacha_type is not None
        and flattened.get("default_gacha_type")
        and flattened.get("default_gacha_type") != str(gacha_type)
    ):
        return {}
    flattened["_endpoint"] = urllib.parse.urlunsplit(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "")
    )
    return flattened


def get_history_params_from_cache(cache_path, gacha_type=None):
    for source_path in _source_paths(cache_path):
        if not os.path.exists(source_path):
            continue

        try:
            with open(source_path, "rb") as source_file:
                params = _get_query_params(source_file.read(), gacha_type)
            if params.get("authkey"):
                return params
        except (OSError, UnicodeError) as error:
            print(f"Error reading authkey source: {error}")

    return {}


def get_authkey_from_cache(cache_path, gacha_type=None):
    return get_history_params_from_cache(cache_path, gacha_type).get("authkey")