import threading
import time

import customtkinter as ctk

from config import GAME_CONFIGS
from extractors import EXTRACTORS


class PullTrackerWidget(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pull Tracker Widget")
        self.geometry("250x165")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1e1e24")

        self.selected_game = "HSR"
        self.game_tabs = ctk.CTkTabview(self, width=190, height=42, command=self.select_game)
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

        self.status_label = ctk.CTkLabel(self, text="50/50 status unknown", font=("Arial", 12), text_color="#f0c05a")
        self.status_label.pack(pady=(0, 10))

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)

        threading.Thread(target=self.update_data_loop, daemon=True).start()

    def select_game(self):
        self.selected_game = self.game_tabs.get()
        config = GAME_CONFIGS[self.selected_game]
        self.title_label.configure(text=config["title"])
        self.pity_label.configure(text=f"-- / {config['hard_pity']}")
        self.status_label.configure(text="Open in-game history first", text_color="#ff5555")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def update_data_loop(self):
        while True:
            game = self.selected_game
            config = GAME_CONFIGS[game]
            extractor = EXTRACTORS[game]
            authkey = extractor.get_authkey()

            if authkey:
                data = extractor.fetch_pity_data(authkey)
                if "error" in data:
                    self.status_label.configure(text=data["error"], text_color="#ff5555")
                else:
                    self.pity_label.configure(text=f"{data['pity']} / {config['hard_pity']}")
                    status_text = "Guaranteed Limited!" if data["guaranteed"] else "Next 5★ is a 50/50"
                    color = "#55ff55" if data["guaranteed"] else "#f0c05a"
                    self.status_label.configure(text=status_text, text_color=color)
            else:
                self.status_label.configure(text="Open in-game history first", text_color="#ff5555")

            time.sleep(60)