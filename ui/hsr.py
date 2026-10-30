import customtkinter as ctk

from .game_ui import GameUI


class HSRUI(GameUI):
    def configure_rarity_filters(self):
        widget = self.widget
        for child in widget.filter_frame.winfo_children():
            child.destroy()

        widget.filter_vars = {}
        for rarity, rarity_config in widget.get_selected_config()["rarities"].items():
            widget.filter_vars[rarity] = ctk.BooleanVar(value=rarity_config["enabled"])
            checkbox = ctk.CTkCheckBox(
                widget.filter_frame,
                text=rarity_config["label"],
                variable=widget.filter_vars[rarity],
                command=widget.apply_pull_filters,
                text_color=widget.get_rarity_color(rarity, rarity_config["color"]),
                width=72,
            )
            checkbox.pack(side="left", padx=4)

    def show_recent_pulls(self, pulls):
        widget = self.widget
        for child in widget.recent_pulls_frame.winfo_children():
            child.destroy()

        rarity_configs = widget.get_selected_config()["rarities"]
        for pull in pulls:
            rarity_config = rarity_configs.get(str(pull["rank_type"]))
            rank = rarity_config["label"] if rarity_config else str(pull["rank_type"])
            label = ctk.CTkLabel(
                widget.recent_pulls_frame,
                text=f"{pull['time']}  {rank}  {pull['name']}",
                anchor="w",
                text_color=(
                    widget.get_rarity_color(str(pull["rank_type"]), rarity_config["color"])
                    if rarity_config
                    else widget.get_theme()["text"]
                ),
            )
            label.pack(fill="x", padx=4, pady=1)

        if not pulls:
            ctk.CTkLabel(
                widget.recent_pulls_frame,
                text="No pulls match the selected filters.",
                text_color=widget.get_theme()["muted"],
            ).pack(pady=8)