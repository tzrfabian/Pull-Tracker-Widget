import requests
import time


def fetch_pity_data(authkey, config, history_params=None):
    history_params = history_params or {}
    endpoint = history_params.pop(
        "_endpoint",
        "https://api-os-takumi.mihoyo.com/common/gacha_record/api/getGachaLog",
    )
    params = {
        **history_params,
        "authkey_ver": 1,
        "lang": history_params.get("lang", "en"),
        "authkey": authkey,
        "gacha_id": config.get("gacha_id"),
        "region": config.get("region", history_params.get("region", "prod_official_asia")),
        "gacha_type": config["gacha_type"],
        "default_gacha_type": config["gacha_type"],
        "timestamp": int(time.time()),
        "plat_type": "pc",
        "page": 1,
        "size": 20,
        "end_id": 0,
    }

    response = requests.get(endpoint, params=params, timeout=15)
    response.raise_for_status()
    response = response.json()
    if response.get("retcode") != 0:
        if response.get("retcode") == -502:
            return {"error": "HoYoverse rejected this history link. Run the PowerShell extractor again while history is open."}
        return {"error": response.get("message", "AuthKey expired. Open in-game history.")}

    pulls = response["data"]["list"]
    pity_count = 0
    is_guaranteed = False

    for pull in pulls:
        if pull["rank_type"] == "5":
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