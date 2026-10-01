from api import fetch_pity_data as fetch_api_pity_data
from config import GAME_CONFIGS
from .common import get_authkey_from_cache


CONFIG = GAME_CONFIGS["HSR"]


def get_authkey():
    return get_authkey_from_cache(CONFIG["cache_path"])


def fetch_pity_data(authkey):
    return fetch_api_pity_data(authkey, CONFIG)