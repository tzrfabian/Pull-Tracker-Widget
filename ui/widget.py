import threading
from pathlib import Path

import customtkinter as ctk
import requests
from PIL import Image

from config import GAME_CONFIGS
from extractors import EXTRACTORS


class PullTrackerWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pull Tracker Widget")
        self.geometry("420x220")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.88)
        self.configure(fg_color="#1e1e24")

        self.selected_game = "HSR"
        self.selected_banner = "character_event"
        self.drag_handle = ctk.CTkFrame(
            self,
            width=380,
            height=12,
            fg_color="#2b2b32",
            corner_radius=4,
        )
        self.drag_handle.pack(pady=(6, 0))
        self.drag_handle.pack_propagate(False)
        self.drag_handle.bind("<ButtonPress-1>", self.start_move)
        self.drag_handle.bind("<B1-Motion>", self.do_move)
        self.drag_handle.bind("<ButtonRelease-1>", self.stop_move)

        assets_dir = Path(__file__).resolve().parent.parent / "assets"
        self.game_icons = {
            game: self.create_game_icon(assets_dir / f"{game.lower()}_icon.png")
            for game in GAME_CONFIGS
        }
        self.game_tabs = ctk.CTkTabview(self, width=340, height=42, command=self.select_game)
        for game in GAME_CONFIGS:
            self.game_tabs.add(game)
            self.game_tabs._segmented_button._buttons_dict[game].configure(
                image=self.game_icons[game],
                compound="left",
            )
        self.game_tabs.set(self.selected_game)
        self.game_tabs.pack(pady=(8, 0))

        self.banner_selector = ctk.CTkOptionMenu(
            self,
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

        self.close_button = ctk.CTkButton(
            self,
            text="X",
            width=24,
            height=24,
            command=self.destroy,
            fg_color="#3a3a44",
            hover_color="#ff5555",
            text_color="#ffffff",
        )
        self.close_button.place(relx=1.0, x=-8, y=8, anchor="ne")

        self.title_label = ctk.CTkLabel(self, text=self.get_selected_config()["title"], font=("Arial", 14, "bold"), text_color="#a0a0b5")
        self.title_label.pack(pady=(10, 0))

        self.pity_label = ctk.CTkLabel(self, text=f"-- / {self.get_selected_config()['hard_pity']}", font=("Arial", 32, "bold"), text_color="#ffffff")
        self.pity_label.pack()

        self.status_label = ctk.CTkLabel(
            self,
            text="50/50 status unknown",
            width=400,
            wraplength=400,
            font=("Arial", 12),
            text_color="#f0c05a",
        )
        self.status_label.pack(pady=(0, 10))

        self.history_url_entry = ctk.CTkEntry(
            self,
            width=400,
            placeholder_text="Paste history URL here",
        )
        self.history_url_entry.pack(pady=(0, 6))

        self.recent_pulls_frame = ctk.CTkScrollableFrame(
            self,
            width=390,
            height=170,
            label_text="Recent pulls",
        )
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_vars = {}
        self.configure_rarity_filters()

        self.load_button = ctk.CTkButton(
            self,
            text="Use Pasted Link",
            width=150,
            height=28,
            command=self.use_pasted_link,
            fg_color="#3a3a44",
            hover_color="#565666",
            text_color="#ffffff",
        )
        self.load_button.pack(pady=(0, 10))

        self.loading = False
        self.refresh_after_id = None
        self.recent_pulls = []
        self.history_urls = {}
        self.dragging = False

        for drag_widget in (self.title_label, self.pity_label, self.status_label):
            drag_widget.bind("<ButtonPress-1>", self.start_move)
            drag_widget.bind("<B1-Motion>", self.do_move)
            drag_widget.bind("<ButtonRelease-1>", self.stop_move)
        self.after_idle(self.adjust_window_size)

    def get_banner_keys(self):
        return list(GAME_CONFIGS[self.selected_game]["banners"])

    def get_selected_config(self):
        return GAME_CONFIGS[self.selected_game]["banners"][self.selected_banner]

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
        for child in self.filter_frame.winfo_children():
            child.destroy()

        self.filter_vars = {}
        for rarity, rarity_config in self.get_selected_config()["rarities"].items():
            self.filter_vars[rarity] = ctk.BooleanVar(value=rarity_config["enabled"])
            checkbox = ctk.CTkCheckBox(
                self.filter_frame,
                text=rarity_config["label"],
                variable=self.filter_vars[rarity],
                command=self.apply_pull_filters,
                text_color=rarity_config["color"],
                width=72,
            )
            checkbox.pack(side="left", padx=4)

    def select_game(self):
        self.selected_game = self.game_tabs.get()
        self.selected_banner = self.get_banner_keys()[0]
        self.configure_banner_selector()
        self.reset_for_selection()

    def select_banner(self, banner_label):
        self.selected_banner = next(
            key
            for key, config in GAME_CONFIGS[self.selected_game]["banners"].items()
            if config["label"] == banner_label
        )
        self.reset_for_selection()

    def reset_for_selection(self):
        config = self.get_selected_config()
        self.title_label.configure(text=config["title"])
        self.pity_label.configure(text=f"-- / {config['hard_pity']}")
        self.status_label.configure(text="Don't forget open in-game history first", text_color="#ff5555")
        self.recent_pulls_frame.pack_forget()
        self.filter_frame.pack_forget()
        self.configure_rarity_filters()
        self.history_url_entry.pack(pady=(0, 6))
        self.load_button.configure(state="normal", text="Use Pasted Link", command=self.use_pasted_link)
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
            return

        self.loading = True
        self.load_button.configure(state="disabled", text="Loading...")
        self.status_label.configure(text="Reading pull history...", text_color="#a0a0b5")
        game = self.selected_game
        banner = self.selected_banner
        threading.Thread(target=self.fetch_history, args=(game, banner), daemon=True).start()

    def use_pasted_link(self):
        history_url = self.history_url_entry.get().strip() or self.history_urls.get(self.selected_game, "")
        if not history_url:
            self.status_label.configure(text="Paste the in-game history URL first.", text_color="#ff5555")
            return
        if self.loading:
            return

        self.start_pasted_history(history_url, "Loading pasted history...")

    def start_pasted_history(self, history_url, status_text, allow_gacha_type_mismatch=False):
        if self.loading:
            return
        self.loading = True
        self.load_button.configure(state="disabled", text="Loading...")
        self.status_label.configure(text=status_text, text_color="#a0a0b5")
        game = self.selected_game
        banner = self.selected_banner
        threading.Thread(
            target=self.fetch_pasted_history,
            args=(game, banner, history_url, allow_gacha_type_mismatch),
            daemon=True,
        ).start()

    def fetch_pasted_history(self, game, banner, history_url, allow_gacha_type_mismatch=False):
        extractor = EXTRACTORS[game]
        banner_config = GAME_CONFIGS[game]["banners"][banner]
        try:
            result = extractor.fetch_pity_data_from_url(
                history_url,
                banner_config,
                allow_gacha_type_mismatch=allow_gacha_type_mismatch,
            )
        except (OSError, UnicodeError, requests.RequestException, ValueError, KeyError, TypeError) as error:
            result = {"error": f"Unable to load history: {error}"}
        self.after(0, self.show_history_result, game, banner, result, history_url)

    def fetch_history(self, game, banner):
        banner_config = GAME_CONFIGS[game]["banners"][banner]
        extractor = EXTRACTORS[game]

        try:
            authkey = extractor.get_authkey(banner_config)
            if not authkey:
                result = {"error": "History source not found. Reopen in-game history."}
            else:
                result = extractor.fetch_pity_data(authkey, banner_config)
        except (OSError, UnicodeError, requests.RequestException, ValueError, KeyError, TypeError) as error:
            result = {"error": f"Unable to load history: {error}"}

        self.after(0, self.show_history_result, game, banner, result)

    def show_history_result(self, game, banner, data, history_url=None):
        if game != self.selected_game or banner != self.selected_banner:
            return

        config = self.get_selected_config()
        self.loading = False
        self.load_button.configure(state="normal", text="Use Pasted Link")

        if "error" in data:
            self.status_label.configure(text=data["error"], text_color="#ff5555")
        else:
            if history_url:
                self.history_urls[game] = history_url
            self.pity_label.configure(text=f"{data['pity']} / {config['hard_pity']}")
            status_text = (
                "Guaranteed Limited!"
                if data["guaranteed"]
                else f"Next {config['highest_rarity_label']} is a 50/50"
            )
            color = "#55ff55" if data["guaranteed"] else "#f0c05a"
            self.status_label.configure(text=status_text, text_color=color)
            self.recent_pulls = data["recent_pulls"]
            self.show_recent_pulls(self.get_filtered_pulls())
            self.history_url_entry.pack_forget()
            self.filter_frame.pack(pady=(0, 4))
            self.recent_pulls_frame.pack(pady=(0, 6))
            self.load_button.configure(text="Submit Link Again", command=self.show_link_input)
            self.adjust_window_size()

        self.refresh_after_id = self.after(60000, self.refresh_history)

    def show_recent_pulls(self, pulls):
        for child in self.recent_pulls_frame.winfo_children():
            child.destroy()

        rarity_configs = self.get_selected_config()["rarities"]
        for pull in pulls:
            rarity_config = rarity_configs.get(str(pull["rank_type"]))
            rank = rarity_config["label"] if rarity_config else str(pull["rank_type"])
            label = ctk.CTkLabel(
                self.recent_pulls_frame,
                text=f"{pull['time']}  {rank}  {pull['name']}",
                anchor="w",
                text_color=rarity_config["color"] if rarity_config else "#ffffff",
            )
            label.pack(fill="x", padx=4, pady=1)

        if not pulls:
            ctk.CTkLabel(
                self.recent_pulls_frame,
                text="No pulls match the selected filters.",
                text_color="#a0a0b5",
            ).pack(pady=8)

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
        self.load_button.configure(text="Use Pasted Link", command=self.use_pasted_link)
        self.status_label.configure(text="Paste a new history URL.", text_color="#a0a0b5")
        self.adjust_window_size()

    def adjust_window_size(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = max(420, self.winfo_reqwidth() + 16)
        height = min(self.winfo_reqheight() + 16, screen_height - 20)
        x = min(max(0, self.winfo_x()), max(0, screen_width - width))
        y = min(max(0, self.winfo_y()), max(0, screen_height - height))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def refresh_history(self):
        self.refresh_after_id = None
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
