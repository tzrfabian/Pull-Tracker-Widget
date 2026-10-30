import logging
import subprocess
import threading
import urllib.parse
from pathlib import Path

import customtkinter as ctk
import requests
from PIL import Image

from config import GAME_CONFIGS
from extractors import EXTRACTORS
from ui.hsr import HSRUI
from ui.zzz import ZZZUI


logger = logging.getLogger(__name__)

GAME_UIS = {
    "HSR": HSRUI,
    "ZZZ": ZZZUI,
}


class PullTrackerWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pull Tracker Widget")
        self.geometry("420x220")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.88)
        self.selected_game = "HSR"
        self.selected_banner = "character_event"
        self.game_ui = GAME_UIS[self.selected_game](self)
        theme = self.get_theme()
        self.configure(fg_color=theme["background"])
        self.minimized = False
        self.header = ctk.CTkFrame(
            self,
            height=34,
            fg_color=theme["surface"],
            corner_radius=4,
        )
        self.header.pack(fill="x", padx=6, pady=(6, 0))
        self.header.pack_propagate(False)
        self.header_title = ctk.CTkLabel(
            self.header,
            text="Pull Tracker Widget",
            font=("Arial", 12, "bold"),
            text_color=theme["text"],
        )
        self.header_title.pack(side="left", padx=10)


        self.close_button = ctk.CTkButton(
            self.header,
            text="X",
            width=28,
            height=24,
            command=self.destroy,
            fg_color="transparent",
            hover_color=theme["error"],
            text_color=theme["text"],
        )
        self.close_button.pack(side="right", padx=(0, 6), pady=5)
        
        self.minimize_button = ctk.CTkButton(
            self.header,
            text="—",
            width=28,
            height=24,
            command=self.toggle_minimize,
            fg_color="transparent",
            hover_color=theme["surface_alt"],
            text_color=theme["text"],
        )
        self.minimize_button.pack(side="right", padx=(0, 2), pady=5)

        for drag_widget in (self.header, self.header_title):
            drag_widget.bind("<ButtonPress-1>", self.start_move)
            drag_widget.bind("<B1-Motion>", self.do_move)
            drag_widget.bind("<ButtonRelease-1>", self.stop_move)

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

        assets_dir = Path(__file__).resolve().parent.parent / "assets"
        self.game_icons = {
            game: self.create_game_icon(assets_dir / f"{game.lower()}_icon.png")
            for game in GAME_CONFIGS
        }
        self.game_tabs = ctk.CTkTabview(self.content_frame, width=340, height=42, command=self.select_game)
        for game in GAME_CONFIGS:
            self.game_tabs.add(game)
            self.game_tabs._segmented_button._buttons_dict[game].configure(
                image=self.game_icons[game],
                compound="left",
            )
        self.game_tabs.set(self.selected_game)
        self.game_tabs.pack(pady=(8, 0))

        self.banner_selector = ctk.CTkOptionMenu(
            self.content_frame,
            values=[
                banner_config["label"]
                for banner_config in GAME_CONFIGS[self.selected_game]["banners"].values()
            ],
            command=self.select_banner,
            width=340,
            height=28,
        )
        self.banner_selector.set(self.get_selected_config()["label"])
        self.banner_selector.pack(pady=(4, 0))

        self.title_label = ctk.CTkLabel(self.content_frame, text=self.get_selected_config()["title"], font=("Arial", 14, "bold"), text_color=theme["muted"])
        self.title_label.pack(pady=(10, 0))

        self.pity_label = ctk.CTkLabel(self.content_frame, text=f"-- / {self.get_selected_config()['hard_pity']}", font=("Arial", 32, "bold"), text_color=theme["text"])
        self.pity_label.pack()

        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="50/50 status unknown",
            width=400,
            wraplength=400,
            font=("Arial", 12),
            text_color=theme["secondary"],
        )
        self.status_label.pack(pady=(0, 10))

        self.history_url_entry = ctk.CTkEntry(
            self.content_frame,
            width=400,
            placeholder_text="Paste history URL here",
        )
        self.load_button = ctk.CTkButton(
            self.content_frame,
            text="Load from Game",
            width=180,
            height=28,
            command=self.load_history,
            fg_color=theme["accent"],
            hover_color=theme["accent_hover"],
            text_color=theme["text"],
        )
        self.load_button.pack(pady=(0, 4))

        self.pasted_load_button = ctk.CTkButton(
            self.content_frame,
            text="Use Pasted Link",
            width=180,
            height=28,
            command=self.handle_pasted_link,
            fg_color="transparent",
            hover_color=theme["surface_alt"],
            text_color=theme["text"],
        )
        self.pasted_load_button.pack(pady=(0, 6))

        self.recent_pulls_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            width=390,
            height=170,
            label_text="Recent pulls",
        )
        self.filter_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.filter_vars = {}
        self.configure_rarity_filters()

        self.loading = False
        self.refresh_after_id = None
        self.recent_pulls = []
        self.history_urls = {}
        self.history_sources = {}
        self.dragging = False
        self.apply_game_theme()

        for drag_widget in (self.title_label, self.pity_label, self.status_label):
            drag_widget.bind("<ButtonPress-1>", self.start_move)
            drag_widget.bind("<B1-Motion>", self.do_move)
            drag_widget.bind("<ButtonRelease-1>", self.stop_move)
        self.after_idle(self.adjust_window_size)

    def get_banner_keys(self):
        return list(GAME_CONFIGS[self.selected_game]["banners"])

    def get_selected_config(self):
        return GAME_CONFIGS[self.selected_game]["banners"][self.selected_banner]

    def get_theme(self):
        return GAME_CONFIGS[self.selected_game]["theme"]

    def get_rarity_color(self, rarity, fallback):
        return self.get_theme()["rarities"].get(str(rarity), fallback)

    def apply_game_theme(self):
        theme = self.get_theme()
        self.configure(fg_color=theme["background"])
        self.header.configure(fg_color=theme["surface"])
        self.header_title.configure(text_color=theme["text"])
        self.close_button.configure(
            hover_color=theme["error"],
            text_color=theme["text"],
        )
        self.minimize_button.configure(
            hover_color=theme["surface_alt"],
            text_color=theme["text"],
        )
        self.game_tabs.configure(
            fg_color=theme["background"],
            segmented_button_fg_color=theme["surface"],
            segmented_button_selected_color=theme["accent"],
            segmented_button_selected_hover_color=theme["accent_hover"],
            text_color=theme["text"],
        )
        for button in self.game_tabs._segmented_button._buttons_dict.values():
            button.configure(
                fg_color=theme["surface"],
                hover_color=theme["surface_alt"],
                text_color=theme["text"],
            )
        self.banner_selector.configure(
            fg_color=theme["surface"],
            button_color=theme["accent"],
            button_hover_color=theme["accent_hover"],
            text_color=theme["text"],
        )
        self.title_label.configure(text_color=theme["muted"])
        self.pity_label.configure(text_color=theme["text"])
        self.status_label.configure(text_color=theme["muted"])
        self.history_url_entry.configure(
            fg_color=theme["surface"],
            border_color=theme["accent"],
            text_color=theme["text"],
            placeholder_text_color=theme["muted"],
        )
        self.load_button.configure(
            fg_color=theme["accent"],
            hover_color=theme["accent_hover"],
            text_color=theme["text"],
        )
        self.pasted_load_button.configure(
            hover_color=theme["surface_alt"],
            text_color=theme["text"],
        )
        self.recent_pulls_frame.configure(
            fg_color=theme["surface"],
            label_fg_color=theme["surface_alt"],
            label_text_color=theme["text"],
        )

    def configure_banner_selector(self):
        banner_configs = GAME_CONFIGS[self.selected_game]["banners"]
        self.banner_selector.configure(
            values=[banner_config["label"] for banner_config in banner_configs.values()]
        )
        self.banner_selector.set(banner_configs[self.selected_banner]["label"])

    @staticmethod
    def create_game_icon(path):
        with Image.open(path) as source:
            icon = source.convert("RGBA")
        icon.thumbnail((22, 22), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (22, 22))
        canvas.alpha_composite(
            icon,
            ((22 - icon.width) // 2, (22 - icon.height) // 2),
        )
        return ctk.CTkImage(light_image=canvas, dark_image=canvas, size=(22, 22))

    def configure_rarity_filters(self):
        self.game_ui.configure_rarity_filters()

    def select_game(self):
        self.selected_game = self.game_tabs.get()
        self.selected_banner = self.get_banner_keys()[0]
        self.game_ui = GAME_UIS[self.selected_game](self)
        logger.debug("Selected game=%s banner=%s", self.selected_game, self.selected_banner)
        self.apply_game_theme()
        self.configure_banner_selector()
        self.reset_for_selection()

    def select_banner(self, banner_label):
        self.selected_banner = next(
            key
            for key, config in GAME_CONFIGS[self.selected_game]["banners"].items()
            if config["label"] == banner_label
        )
        logger.debug("Selected game=%s banner=%s", self.selected_game, self.selected_banner)
        self.reset_for_selection()

    def reset_for_selection(self):
        config = self.get_selected_config()
        self.title_label.configure(text=config["title"])
        self.pity_label.configure(text=f"-- / {config['hard_pity']}")
        self.status_label.configure(
            text="Don't forget open in-game history first",
            text_color=self.get_theme()["error"],
        )
        self.recent_pulls_frame.pack_forget()
        self.filter_frame.pack_forget()
        self.configure_rarity_filters()
        self.history_url_entry.pack_forget()
        self.load_button.configure(state="normal", text="Load from Game", command=self.load_history)
        self.pasted_load_button.configure(state="normal", text="Use Pasted Link", command=self.handle_pasted_link)
        self.loading = False
        if self.refresh_after_id is not None:
            self.after_cancel(self.refresh_after_id)
            self.refresh_after_id = None
        saved_history_url = self.history_urls.get(self.selected_game)
        if saved_history_url:
            self.start_pasted_history(
                saved_history_url,
                "Loading selected banner...",
                allow_gacha_type_mismatch=True,
            )
        self.adjust_window_size()

    def load_history(self):
        if self.loading:
            logger.debug("Ignoring local load request because another load is active")
            return

        logger.info("Starting PowerShell history load: game=%s banner=%s", self.selected_game, self.selected_banner)
        self.loading = True
        self.load_button.configure(state="disabled", text="Loading...")
        self.pasted_load_button.configure(state="disabled")
        self.status_label.configure(
            text="Running extractor in PowerShell...",
            text_color=self.get_theme()["muted"],
        )
        game = self.selected_game
        banner = self.selected_banner
        self.history_sources[game] = "powershell"
        threading.Thread(target=self.fetch_history_from_powershell, args=(game, banner), daemon=True).start()

    def use_pasted_link(self):
        history_url = self.history_url_entry.get().strip() or self.history_urls.get(self.selected_game, "")
        if not history_url:
            logger.warning("Pasted-link load requested without a history URL")
            self.status_label.configure(
                text="Paste the in-game history URL first.",
                text_color=self.get_theme()["error"],
            )
            return
        if self.loading:
            return

        self.start_pasted_history(history_url, "Loading pasted history...")

    def start_pasted_history(self, history_url, status_text, allow_gacha_type_mismatch=False):
        if self.loading:
            logger.debug("Ignoring pasted-link request because another load is active")
            return

        logger.info(
            "Starting pasted history load: game=%s banner=%s allow_gacha_type_mismatch=%s",
            self.selected_game,
            self.selected_banner,
            allow_gacha_type_mismatch,
        )
        self.loading = True
        self.load_button.configure(state="disabled", text="Loading...")
        self.pasted_load_button.configure(state="disabled")
        self.status_label.configure(text=status_text, text_color=self.get_theme()["muted"])
        game = self.selected_game
        banner = self.selected_banner
        self.history_sources[game] = "pasted"
        threading.Thread(
            target=self.fetch_pasted_history,
            args=(game, banner, history_url, allow_gacha_type_mismatch),
            daemon=True,
        ).start()

    def fetch_pasted_history(self, game, banner, history_url, allow_gacha_type_mismatch=False):
        extractor = EXTRACTORS[game]
        banner_config = GAME_CONFIGS[game]["banners"][banner]
        logger.debug("Reading pasted history with extractor: game=%s banner=%s", game, banner)
        try:
            result = extractor.fetch_pity_data_from_url(
                history_url,
                banner_config,
                allow_gacha_type_mismatch=allow_gacha_type_mismatch,
            )
        except (OSError, UnicodeError, requests.RequestException, ValueError, KeyError, TypeError) as error:
            logger.exception("Pasted history load failed: game=%s banner=%s", game, banner)
            result = {"error": f"Unable to load history: {error}"}
        logger.debug("Pasted history worker completed: game=%s success=%s", game, "error" not in result)
        self.after(0, self.show_history_result, game, banner, result, history_url)

    def fetch_history(self, game, banner):
        banner_config = GAME_CONFIGS[game]["banners"][banner]
        extractor = EXTRACTORS[game]
        logger.debug("Reading local game history source: game=%s banner=%s", game, banner)

        try:
            authkey = extractor.get_authkey(banner_config)
            if not authkey:
                logger.warning("No authkey found in local game sources: game=%s banner=%s", game, banner)
                result = {"error": "History source not found. Reopen in-game history."}
            else:
                logger.debug("Authkey found; requesting history API: game=%s banner=%s", game, banner)
                result = extractor.fetch_pity_data(authkey, banner_config)
        except (OSError, UnicodeError, requests.RequestException, ValueError, KeyError, TypeError) as error:
            logger.exception("Local history load failed: game=%s banner=%s", game, banner)
            result = {"error": f"Unable to load history: {error}"}

        logger.debug("Local history worker completed: game=%s success=%s", game, "error" not in result)
        self.after(0, self.show_history_result, game, banner, result)

    def fetch_history_from_powershell(self, game, banner):
        extractor_config = GAME_CONFIGS[game]
        banner_config = extractor_config["banners"][banner]
        command = extractor_config["extractor_command"]
        try:
            logger.info("Launching visible PowerShell extractor: game=%s banner=%s", game, banner)
            subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                check=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            clipboard_result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            history_url = clipboard_result.stdout.strip()
            parsed_url = urllib.parse.urlsplit(history_url)
            query = urllib.parse.parse_qs(parsed_url.query)
            if not parsed_url.scheme or not parsed_url.netloc or not query.get("authkey"):
                raise ValueError("PowerShell did not copy a valid history URL to the clipboard.")
            logger.info("PowerShell copied a valid history URL: game=%s banner=%s", game, banner)
            result = EXTRACTORS[game].fetch_pity_data_from_url(history_url, banner_config)
        except (
            OSError,
            subprocess.SubprocessError,
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            logger.exception("PowerShell history load failed: game=%s banner=%s", game, banner)
            result = {"error": f"Unable to load history from PowerShell: {error}"}

        logger.debug("PowerShell history worker completed: game=%s success=%s", game, "error" not in result)
        self.after(0, self.show_history_result, game, banner, result, history_url if "history_url" in locals() else None)

    def show_history_result(self, game, banner, data, history_url=None):
        if game != self.selected_game or banner != self.selected_banner:
            logger.debug(
                "Ignoring stale history result: result=%s/%s current=%s/%s",
                game,
                banner,
                self.selected_game,
                self.selected_banner,
            )
            return

        logger.debug("Displaying history result: game=%s banner=%s success=%s", game, banner, "error" not in data)
        config = self.get_selected_config()
        self.loading = False
        self.load_button.configure(state="normal", text="Load from Game", command=self.load_history)
        self.pasted_load_button.configure(state="normal", text="Use Pasted Link", command=self.handle_pasted_link)

        if "error" in data:
            logger.error("History load returned an error: game=%s banner=%s error=%s", game, banner, data["error"])
            self.status_label.configure(
                text=data["error"],
                text_color=self.get_theme()["error"],
            )
        else:
            if history_url:
                self.history_urls[game] = history_url
            self.pity_label.configure(text=f"{data['pity']} / {config['hard_pity']}")
            status_text = (
                "Guaranteed Limited!"
                if data["guaranteed"]
                else f"Next {config['highest_rarity_label']} is a 50/50"
            )
            color = (
                self.get_theme()["success"]
                if data["guaranteed"]
                else self.get_theme()["secondary"]
            )
            self.status_label.configure(text=status_text, text_color=color)
            self.recent_pulls = data["recent_pulls"]
            self.show_recent_pulls(self.get_filtered_pulls())
            self.history_url_entry.pack_forget()
            self.filter_frame.pack(pady=(0, 4))
            self.recent_pulls_frame.pack(pady=(0, 6))
            self.load_button.configure(text="Load from Game", command=self.load_history)
            self.pasted_load_button.configure(text="Use Pasted Link", command=self.handle_pasted_link)
            self.adjust_window_size()

        self.refresh_after_id = self.after(60000, self.refresh_history)

    def show_recent_pulls(self, pulls):
        self.game_ui.show_recent_pulls(pulls)

    def apply_pull_filters(self):
        self.show_recent_pulls(self.get_filtered_pulls())
        self.adjust_window_size()

    def get_filtered_pulls(self):
        selected_rarities = {
            rarity for rarity, variable in self.filter_vars.items() if variable.get()
        }
        return [
            pull for pull in self.recent_pulls
            if str(pull["rank_type"]) in selected_rarities
        ]

    def show_link_input(self):
        if self.refresh_after_id is not None:
            self.after_cancel(self.refresh_after_id)
            self.refresh_after_id = None
        self.recent_pulls_frame.pack_forget()
        self.filter_frame.pack_forget()
        self.history_url_entry.pack(pady=(0, 6))
        self.load_button.configure(text="Load from Game", command=self.load_history)
        self.pasted_load_button.configure(
            state="normal",
            text="Use Pasted Link",
            command=self.use_pasted_link,
        )
        self.status_label.configure(
            text="Paste a new history URL.",
            text_color=self.get_theme()["muted"],
        )
        self.adjust_window_size()

    def handle_pasted_link(self):
        if self.history_url_entry.winfo_manager():
            self.use_pasted_link()
        else:
            self.show_link_input()

    def adjust_window_size(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if self.minimized:
            width = max(220, self.header.winfo_reqwidth() + 12)
            height = self.header.winfo_reqheight() + 12
        else:
            width = max(420, self.winfo_reqwidth() + 16)
            height = min(self.winfo_reqheight() + 16, screen_height - 20)
        x = min(max(0, self.winfo_x()), max(0, screen_width - width))
        y = min(max(0, self.winfo_y()), max(0, screen_height - height))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def toggle_minimize(self):
        self.minimized = not self.minimized
        if self.minimized:
            self.content_frame.pack_forget()
            self.minimize_button.configure(text="⤢")
        else:
            self.content_frame.pack(fill="both", expand=True)
            self.minimize_button.configure(text="—")
        self.adjust_window_size()

    def refresh_history(self):
        self.refresh_after_id = None
        logger.debug("Refreshing history: game=%s source=%s", self.selected_game, self.history_sources.get(self.selected_game))
        if self.history_sources.get(self.selected_game) in {"local", "powershell"}:
            self.load_history()
        else:
            self.use_pasted_link()

    def start_move(self, event):
        self.dragging = True
        self.x = event.x_root
        self.y = event.y_root

    def do_move(self, event):
        if not self.dragging:
            return
        deltax = event.x_root - self.x
        deltay = event.y_root - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
        self.x = event.x_root
        self.y = event.y_root

    def stop_move(self, _event):
        self.dragging = False
