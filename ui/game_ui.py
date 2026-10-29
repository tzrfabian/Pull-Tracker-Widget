from abc import ABC, abstractmethod


class GameUI(ABC):
    def __init__(self, widget):
        self.widget = widget

    @abstractmethod
    def configure_rarity_filters(self):
        """Create the rarity controls for the selected game's banner."""

    @abstractmethod
    def show_recent_pulls(self, pulls):
        """Render the selected game's recent pulls."""