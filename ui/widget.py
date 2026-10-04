import threading

import customtkinter as ctk
import requests

from config import GAME_CONFIGS
from extractors import EXTRACTORS


class PullTrackerWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pull Tracker Widget")
        self.geometry("420x220")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1e1e24")

        self.selected_game = "HSR"
        self.game_tabs = ctk.CTkTabview(self, width=340, height=42, command=self.select_game)
        self.game_tabs.add("HSR")
        self.game_tabs.add("ZZZ")
        self.game_tabs.set(self.selected_game)
        self.game_tabs.pack(pady=(8, 0))

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

        self.title_label = ctk.CTkLabel(self, text=GAME_CONFIGS[self.selected_game]["title"], font=("Arial", 14, "bold"), text_color="#a0a0b5")
        self.title_label.pack(pady=(10, 0))

        self.pity_label = ctk.CTkLabel(self, text="-- / 90", font=("Arial", 32, "bold"), text_color="#ffffff")
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
        self.filter_vars = {
            "3": ctk.BooleanVar(value=False),
            "4": ctk.BooleanVar(value=True),
            "5": ctk.BooleanVar(value=True),
        }
        for rarity, color in (("3", "#6fa8dc"), ("4", "#b58bd9"), ("5", "#f0c05a")):
            checkbox = ctk.CTkCheckBox(
                self.filter_frame,
                text=f"{rarity}★",
                variable=self.filter_vars[rarity],
                command=self.apply_pull_filters,
                text_color=color,
                width=72,
            )
            checkbox.pack(side="left", padx=4)

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

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        self.after_idle(self.adjust_window_size)

    def select_game(self):
        self.selected_game = self.game_tabs.get()
        config = GAME_CONFIGS[self.selected_game]
        self.title_label.configure(text=config["title"])
        self.pity_label.configure(text=f"-- / {config['hard_pity']}")
        self.status_label.configure(text="Open in-game history first", text_color="#ff5555")
        self.recent_pulls_frame.pack_forget()
        self.filter_frame.pack_forget()
        self.filter_vars["3"].set(False)
        self.filter_vars["4"].set(True)
        self.filter_vars["5"].set(True)
        self.history_url_entry.pack(pady=(0, 6))
        self.load_button.configure(state="normal", text="Use Pasted Link", command=self.use_pasted_link)
        self.loading = False
        if self.refresh_after_id is not None:
            self.after_cancel(self.refresh_after_id)
            self.refresh_after_id = None
        self.adjust_window_size()

    def load_history(self):
        if self.loading:
            return

        self.loading = True
        self.load_button.configure(state="disabled", text="Loading...")
        self.status_label.configure(text="Reading pull history...", text_color="#a0a0b5")
        game = self.selected_game
        threading.Thread(target=self.fetch_history, args=(game,), daemon=True).start()

    def use_pasted_link(self):
        history_url = self.history_url_entry.get().strip()
        if not history_url:
            self.status_label.configure(text="Paste the in-game history URL first.", text_color="#ff5555")
            return
        if self.loading:
            return

        self.loading = True
        self.load_button.configure(state="disabled", text="Loading...")
        self.status_label.configure(text="Loading pasted history...", text_color="#a0a0b5")
        game = self.selected_game
        threading.Thread(target=self.fetch_pasted_history, args=(game, history_url), daemon=True).start()

    def fetch_pasted_history(self, game, history_url):
        extractor = EXTRACTORS[game]
        try:
            result = extractor.fetch_pity_data_from_url(history_url)
        except (OSError, UnicodeError, requests.RequestException, ValueError, KeyError, TypeError) as error:
            result = {"error": f"Unable to load history: {error}"}
        self.after(0, self.show_history_result, game, result)

    def fetch_history(self, game):
        config = GAME_CONFIGS[game]
        extractor = EXTRACTORS[game]

        try:
            authkey = extractor.get_authkey()
            if not authkey:
                result = {"error": "History source not found. Reopen in-game history."}
            else:
                result = extractor.fetch_pity_data(authkey)
        except (OSError, UnicodeError, requests.RequestException, ValueError, KeyError, TypeError) as error:
            result = {"error": f"Unable to load history: {error}"}

        self.after(0, self.show_history_result, game, result)

    def show_history_result(self, game, data):
        if game != self.selected_game:
            return

        config = GAME_CONFIGS[game]
        self.loading = False
        self.load_button.configure(state="normal", text="Use Pasted Link")

        if "error" in data:
            self.status_label.configure(text=data["error"], text_color="#ff5555")
        else:
            self.pity_label.configure(text=f"{data['pity']} / {config['hard_pity']}")
            status_text = "Guaranteed Limited!" if data["guaranteed"] else "Next 5★ is a 50/50"
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

        rarity_colors = {
            "3": "#6fa8dc",
            "4": "#b58bd9",
            "5": "#f0c05a",
        }
        for pull in pulls:
            rank = f"{pull['rank_type']}★"
            label = ctk.CTkLabel(
                self.recent_pulls_frame,
                text=f"{pull['time']}  {rank}  {pull['name']}",
                anchor="w",
                text_color=rarity_colors.get(str(pull["rank_type"]), "#ffffff"),
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
        if self.is_scroll_event(event):
            return "break"
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        if self.is_scroll_event(event):
            return "break"
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def is_scroll_event(self, event):
        widget = event.widget
        while widget is not None:
            if widget == self.recent_pulls_frame:
                return True
            if "scrollbar" in widget.winfo_class().lower():
                return True
            parent_name = widget.winfo_parent()
            if not parent_name:
                break
            widget = self.nametowidget(parent_name)
        return False
