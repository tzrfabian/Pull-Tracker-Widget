from api import fetch_pity_data as fetch_api_pity_data
from config import GAME_CONFIGS
from .common import get_authkey_from_cache, get_history_params_from_cache, get_history_params_from_url


GAME_CONFIG = GAME_CONFIGS["HSR"]


def get_authkey(banner_config):
    return get_authkey_from_cache(GAME_CONFIG["cache_path"], banner_config["gacha_type"])


def fetch_pity_data(authkey, banner_config):
    params = get_history_params_from_cache(GAME_CONFIG["cache_path"], banner_config["gacha_type"])
    return fetch_api_pity_data(authkey, {**GAME_CONFIG, **banner_config}, params)


def fetch_pity_data_from_url(history_url, banner_config, allow_gacha_type_mismatch=False):
    params = get_history_params_from_url(
        history_url,
        banner_config["gacha_type"],
        validate_gacha_type=not allow_gacha_type_mismatch,
    )
    if not params:
        return {"error": f"Invalid HSR {banner_config['label']} URL."}
    return fetch_api_pity_data(params["authkey"], {**GAME_CONFIG, **banner_config}, params)