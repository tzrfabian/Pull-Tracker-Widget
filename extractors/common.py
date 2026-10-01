import os
import re
import urllib.parse


def get_authkey_from_cache(cache_path):
    user_profile = os.environ.get("USERPROFILE", "")
    full_cache_path = os.path.join(user_profile, cache_path)

    if not os.path.exists(full_cache_path):
        return None

    try:
        with open(full_cache_path, "rb") as cache_file:
            data = cache_file.read().decode("utf-8", errors="ignore")

        match = re.search(r'https://api-os-takumi\.mihoyo\.com/common/gacha_record/api/getGachaLog\?([^"]+)', data)
        if match:
            parsed_params = urllib.parse.parse_qs(match.group(1))
            return parsed_params.get("authkey", [None])[0]
    except (OSError, UnicodeError) as error:
        print(f"Error reading cache: {error}")

    return None