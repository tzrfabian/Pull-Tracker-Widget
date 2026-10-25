import logging

from ui.widget import PullTrackerWidget


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.getLogger(__name__).debug("Starting Pull Tracker Widget")
    app = PullTrackerWidget()
    app.mainloop()