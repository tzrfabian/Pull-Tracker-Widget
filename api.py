import requests


def fetch_pity_data(authkey, config):
    endpoint = "https://api-os-takumi.mihoyo.com/common/gacha_record/api/getGachaLog"
    params = {
        "authkey_ver": 1,
        "lang": "en",
        "authkey": authkey,
        "gacha_type": config["gacha_type"],
        "page": 1,
        "size": 20,
    }

    response = requests.get(endpoint, params=params).json()
    if response.get("retcode") != 0:
        return {"error": response.get("message", "AuthKey expired. Open in-game history.")}

    pulls = response["data"]["list"]
    pity_count = 0
    is_guaranteed = False

    for pull in pulls:
        if pull["rank_type"] == "5":
            is_guaranteed = pull["name"] in config["standard_characters"]
            break
        pity_count += 1

    return {"pity": pity_count, "guaranteed": is_guaranteed}