# Pull Tracker Widget

A small, borderless, always-on-top desktop widget for Honkai: Star Rail and Zenless Zone Zero banner pity.

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

The widget starts at `420x280`, stays above other windows, and can be dragged by holding the left mouse button anywhere on it. Use the `HSR` and `ZZZ` tabs to choose the game.

## Setup and refresh

1. Select the game tab.
2. Open that game and open its character event or signal search history.
3. Leave the history available, then run the official Star Rail Station PowerShell extractor below.
4. Paste the URL copied to your clipboard into the widget.
5. Press **Use Pasted Link**.

The extractor validates the URL with the game API, creates a fresh usable history URL, and copies it to your clipboard:

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; Invoke-Expression (New-Object Net.WebClient).DownloadString("https://gist.githubusercontent.com/Star-Rail-Station/2512df54c4f35d399cc9abbde665e8f0/raw/get_warp_link_os.ps1?cachebust=srs")
```

This command is for the Windows Star Rail client. It opens the cache, checks the link, and reports whether the URL was copied. The URL contains a temporary authkey; paste it only into this widget and do not share it.

The script looks for the authkey in the cache file below. On newer game versions where that cache file is not present, it also reads the game's `Player.log` beside the `Data` folder.

HSR:

```text
%USERPROFILE%\AppData\LocalLow\Cognosphere\Star Rail\Data\webCaches\Cache\Cache_Data\data_2
```

ZZZ:

```text
%USERPROFILE%\AppData\LocalLow\miHoYo\ZenlessZoneZero\Data\webCaches\Cache\Cache_Data\data_2
```

The widget checks the API every 60 seconds after a pasted link is loaded. If the link expires, run the extractor again and paste the new URL.

## Current behavior

- Reads HSR character event warp history (`gacha_type=11`) or ZZZ signal search history (`gacha_type=2`), based on the selected tab.
- Displays pity as pulls since the latest 5-star, up to the 90-pull hard pity limit.
- Marks the next limited 5-star as guaranteed after a loss to one of the seven standard 5-star characters.
- Requests only the first 20 history entries. Older history is not searched, so pity and guarantee status can be incomplete when the latest 5-star is not on the first page.
- Shows API or cache errors in the status line.

## Notes

The widget uses the pasted URL and the official HoYoverse API endpoint. The extractor is an external PowerShell script maintained by Star Rail Station; review it before running if you prefer not to execute downloaded scripts.

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