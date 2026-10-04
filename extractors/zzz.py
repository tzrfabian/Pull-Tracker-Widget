from api import fetch_pity_data as fetch_api_pity_data
from config import GAME_CONFIGS
from .common import get_authkey_from_cache, get_history_params_from_cache, get_history_params_from_url


CONFIG = GAME_CONFIGS["ZZZ"]


def get_authkey():
    return get_authkey_from_cache(CONFIG["cache_path"], CONFIG["gacha_type"])


def fetch_pity_data(authkey):
    params = get_history_params_from_cache(CONFIG["cache_path"], CONFIG["gacha_type"])
    return fetch_api_pity_data(authkey, CONFIG, params)


def fetch_pity_data_from_url(history_url):
    params = get_history_params_from_url(history_url, CONFIG["gacha_type"])
    if not params:
        return {"error": "Invalid ZZZ Signal Search URL."}
    return fetch_api_pity_data(params["authkey"], CONFIG, params)