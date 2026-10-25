import logging
import requests
import time


logger = logging.getLogger(__name__)


def fetch_pity_data(authkey, config, history_params=None):
    history_params = history_params or {}
    endpoint = history_params.pop(
        "_endpoint",
        config["history_endpoint"],
    )
    region = config.get("region") or history_params.get("region")
    params = {
        **history_params,
        "authkey_ver": 1,
        "lang": history_params.get("lang", "en"),
        "authkey": authkey,
        "gacha_id": history_params.get("gacha_id") or config.get("gacha_id"),
        "game_biz": config.get("game_biz"),
        "gacha_type": config["gacha_type"],
        "default_gacha_type": config["gacha_type"],
        "timestamp": int(time.time()),
        "plat_type": "pc",
        "page": 1,
        "size": 20,
        "end_id": 0,
    }
    if region:
        params["region"] = region

    logger.debug(
        "Requesting history API: endpoint=%s gacha_type=%s page=%s size=%s",
        endpoint,
        config["gacha_type"],
        params["page"],
        params["size"],
    )
    response = requests.get(endpoint, params=params, timeout=15)
    response.raise_for_status()
    response = response.json()
    logger.debug("History API response: gacha_type=%s retcode=%s", config["gacha_type"], response.get("retcode"))
    if response.get("retcode") != 0:
        if response.get("retcode") == -502:
            return {"error": "HoYoverse rejected this history link. Run the PowerShell extractor again while history is open."}
        return {"error": response.get("message", "AuthKey expired. Open in-game history.")}

    pulls = response["data"]["list"]
    logger.info("History API returned %s pulls: gacha_type=%s", len(pulls), config["gacha_type"])
    pity_count = 0
    is_guaranteed = False

    for pull in pulls:
        if pull["rank_type"] == config["highest_rarity"]:
            is_guaranteed = pull["name"] in config["standard_characters"]
            break
        pity_count += 1

    recent_pulls = [
        {
            "name": pull["name"],
            "item_type": pull["item_type"],
            "rank_type": pull["rank_type"],
            "time": pull["time"],
        }
        for pull in pulls
    ]
    return {
        "pity": pity_count,
        "guaranteed": is_guaranteed,
        "recent_pulls": recent_pulls,
    }