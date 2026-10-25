# Pull Tracker Widget

Desktop Widget tool for help tracking pull history and Pity for gacha games. (Currently supports Honkai: Star Rail and Zenless Zone Zero.)

## Requirements

- Windows
- Python 3.9 or newer
- An active Honkai: Star Rail or Zenless Zone Zero installation

The recommended setup is to double-click `install.bat`. It creates a local `.venv` virtual environment and installs the dependencies from `requirements.txt`.

To install manually from PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.venv\Scripts\python.exe pull_tracker_widget.py
```

## Setup and refresh

1. Select the game tab and then choose the warp or channel to track from the gacha type dropdown.
2. Open that game and open the selected warp or channel's history.
3. Click **Load from Game** in the widget. The widget opens PowerShell, runs the extractor for the selected game, reads the copied history URL, and loads the data automatically.
4. To enter a URL manually, click **Use Pasted Link** to reveal the URL field.

The widget validates the URL with the game API after PowerShell copies it to the clipboard.

### HSR

Run this while the selected HSR warp history is open:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; Invoke-Expression (New-Object Net.WebClient).DownloadString("https://gist.githubusercontent.com/Star-Rail-Station/2512df54c4f35d399cc9abbde665e8f0/raw/get_warp_link_os.ps1?cachebust=srs")
```

### ZZZ

Run this while the selected ZZZ channel history is open:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; Invoke-Expression (New-Object Net.WebClient).DownloadString("https://gist.github.com/Star-Rail-Station/2147c886045beec7cefc301508bd83d3/raw/d0f2ad962539e52ed56bdcf6972943e9cae6d182/get_signal_link_os.ps1")
```

Each command opens the appropriate game's cache, checks the link, and reports whether the URL was copied. The URL contains a temporary authkey; paste it only into this widget and do not share it.

The URL field is hidden by default. After a successful load, the widget shows the eight most recent pulls. Click **Load from Game** again to rerun PowerShell, or click **Use Pasted Link** to reveal the URL field.
After the first successful submission, switching the warp or channel in the gacha type dropdown automatically reloads the selected banner using the saved history link.

The script looks for the authkey in the cache file below. On newer game versions where that cache file is not present, it also reads the game's `Player.log` beside the `Data` folder.

HSR:

```text
%USERPROFILE%\AppData\LocalLow\Cognosphere\Star Rail\Data\webCaches\Cache\Cache_Data\data_2
```

ZZZ:

```text
%USERPROFILE%\AppData\LocalLow\miHoYo\ZenlessZoneZero\Data\webCaches\Cache\Cache_Data\data_2
```

The widget checks the API every 60 seconds after a history is loaded. PowerShell is rerun on each refresh to obtain a fresh URL.

## Current behavior

- Reads the selected HSR warp: Character Event (`gacha_type=11`), Light Cone Event (`gacha_type=12`), Stellar (`gacha_type=1`), Departure (`gacha_type=2`), Character Collaboration (`gacha_type=21`), or Light Cone Collaboration (`gacha_type=22`); or the selected ZZZ channel: Exclusive (`gacha_type=2001`), Stable (`gacha_type=1`), W-Engine (`gacha_type=3001`), or Bangboo (`gacha_type=5001`).
- Uses the HSR `api-os-takumi` history endpoint and the ZZZ `public-operation-nap-sg` endpoint, including ZZZ's `game_biz=nap_global` parameter.
- Displays pity as pulls since the latest highest-rarity pull, up to the 90-pull hard pity limit.
- Shows all pulls returned by the API after a successful load.
- Filters recent pulls by rarity, with the two highest rarities enabled by default.
- Color-codes HSR pulls as blue for 3★, purple for 4★, and gold for 5★. ZZZ API rank types are labeled and colored blue for B Rank (`2`), purple for A Rank (`3`), and gold for S Rank (`4`).
- Marks the next limited highest-rarity pull as guaranteed after a loss to one of the standard highest-rarity characters.
- Uses the header to drag the widget, minimize the content, or close the widget. Click the minimize button again to restore the content.
- Requests only the first 20 history entries. Older history is not searched, so pity and guarantee status can be incomplete when the latest highest-rarity pull is not on the first page.
- Shows API or cache errors in the status line.

## Notes

The widget opens PowerShell and downloads the external extractor maintained by Star Rail Station. Review the script before using this workflow if you prefer not to execute downloaded scripts.

## Debug logs

Run the widget from PowerShell to see timestamped debug output:

```powershell
.venv\Scripts\python.exe pull_tracker_widget.py
```

The log shows the selected game and banner, PowerShell launch, API request results, pull counts, and full exception details when a load fails. Temporary auth keys and pasted URLs are not printed.

## Project layout

```text
pull_tracker_widget.py        Application launcher
install.bat                    Windows setup helper
requirements.txt               Python dependencies
config.py                      Game settings
api.py                         Shared pity API client
extractors/                    Game-specific cache readers
ui/widget.py                   CustomTkinter interface
```