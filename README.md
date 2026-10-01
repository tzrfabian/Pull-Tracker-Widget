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

The widget starts at `250x165`, stays above other windows, and can be dragged by holding the left mouse button anywhere on it. Use the `HSR` and `ZZZ` tabs to choose the game.

## Setup and refresh

1. Select the game tab.
2. Open that game and open its character event or signal search history.
3. Leave the history available long enough for the game to write its web cache.
4. Start the widget, or wait for its next refresh.

The script looks for the authkey in:

HSR:

```text
%USERPROFILE%\AppData\LocalLow\Cognosphere\Star Rail\Data\webCaches\Cache\Cache_Data\data_2
```

ZZZ:

```text
%USERPROFILE%\AppData\LocalLow\miHoYo\ZenlessZoneZero\Data\webCaches\Cache\Cache_Data\data_2
```

The widget checks the cache and API every 60 seconds. If no authkey is found, open the in-game history again. Authkeys are temporary credentials; do not share the cache file, extracted URL, or screenshots containing them.

## Current behavior

- Reads HSR character event warp history (`gacha_type=11`) or ZZZ signal search history (`gacha_type=2`), based on the selected tab.
- Displays pity as pulls since the latest 5-star, up to the 90-pull hard pity limit.
- Marks the next limited 5-star as guaranteed after a loss to one of the seven standard 5-star characters.
- Requests only the first 20 history entries. Older history is not searched, so pity and guarantee status can be incomplete when the latest 5-star is not on the first page.
- Shows API or cache errors in the status line.

## Notes

The widget uses the game’s locally cached history URL and the official HoYoverse API endpoint. The authkey can expire, in which case opening the in-game history again should generate a fresh one.

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