import logging
import requests
import time


logger = logging.getLogger(__name__)


def _average_pity(pulls, rarity):
    pull_positions = [
        position
        for position, pull in enumerate(reversed(pulls))
        if pull["rank_type"] == rarity
    ]
    if len(pull_positions) < 2:
        return None

    pity_values = [
        current - previous - 1
        for previous, current in zip(pull_positions, pull_positions[1:])
    ]
    return round(sum(pity_values) / len(pity_values), 1)


def _get_statistics(pulls, config):
    highest_rarity = config["highest_rarity"]
    rarity_values = sorted(
        config.get("rarities", {highest_rarity: {}}),
        key=int,
        reverse=True,
    )
    second_highest_rarity = next(
        (rarity for rarity in rarity_values if rarity != highest_rarity),
        None,
    )
    highest_rarity_pulls = [
        pull for pull in pulls if pull["rank_type"] == highest_rarity
    ]
    standard_characters = config["standard_characters"]
    eligible_50_50_pulls = [
        pull
        for pull in highest_rarity_pulls
        if standard_characters
    ]
    wins = sum(
        pull["name"] not in standard_characters
        for pull in eligible_50_50_pulls
    )

    return {
        "total_warps": len(pulls),
        "currency_spent": len(pulls) * config.get("currency_per_warp", 0),
        "highest_rarity_count": len(highest_rarity_pulls),
        "second_highest_rarity_count": (
            sum(pull["rank_type"] == second_highest_rarity for pull in pulls)
            if second_highest_rarity
            else 0
        ),
        "average_highest_rarity_pity": _average_pity(pulls, highest_rarity),
        "average_second_highest_rarity_pity": (
            _average_pity(pulls, second_highest_rarity)
            if second_highest_rarity
            else None
        ),
        "win_rate": (
            round(wins / len(eligible_50_50_pulls) * 100, 2)
            if eligible_50_50_pulls
            else None
        ),
    }


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
        "game_biz": config.get("game_biz") or history_params.get("game_biz"),
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
    pulls = []
    while True:
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
        response = response.json()
        logger.debug(
            "History API response: gacha_type=%s retcode=%s page=%s",
            config["gacha_type"],
            response.get("retcode"),
            params["page"],
        )
        if response.get("retcode") != 0:
            if response.get("retcode") == -502:
                return {"error": "HoYoverse rejected this history link. Run the PowerShell extractor again while history is open."}
            return {"error": response.get("message", "AuthKey expired. Open in-game history.")}

        page_pulls = response["data"]["list"]
        pulls.extend(page_pulls)
        if len(page_pulls) < params["size"]:
            break

        next_end_id = page_pulls[-1].get("id")
        if not next_end_id or next_end_id == params["end_id"]:
            break
        params["page"] += 1
        params["end_id"] = next_end_id

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
        "statistics": _get_statistics(pulls, config),
        "recent_pulls": recent_pulls,
    }