import os
import time
from datetime import date, timedelta
from rich.console import Console
from rich.prompt import Prompt

from tui.config import THEME
from data.database import DatabaseManager

from tui.screens import ScreenManager
from planner_services import PlannerService
from tui.actions import ActionHandler

os.makedirs("data", exist_ok=True)


def run():
    db = DatabaseManager()
    current_date = date.today()

    console = Console(theme=THEME, highlight=False)
    service = PlannerService(db)
    screens = ScreenManager(console, service)
    actions = ActionHandler(console, service)

    try:
        while True:
            today = date.today()
            mode = service.day_mode(current_date)
            day = service.get_or_create_day(current_date)

            if mode == "plan":
                screens.plan(day, current_date)
            elif mode == "today":
                screens.today(day, current_date)
            else:
                screens.reflect(day, current_date)

            console.print()
            try:
                key = Prompt.ask("  [prompt]>[/]", default="").strip()
            except (KeyboardInterrupt, EOFError):
                break

            k = key.lower()

            # navigation
            if k in ("q", "quit"):
                break
            elif k in ("b", "left", "<", "prev"):
                current_date -= timedelta(days=1)
            elif k in ("n", "right", ">", "next"):
                current_date += timedelta(days=1)
            elif k in ("t", "today"):
                current_date = today

            # history browser (capital H)
            elif key == "H" or k in ("history", "hist"):
                picked = screens.history_browser()
                if picked:
                    current_date = picked

            # task actions
            elif k == "a":
                actions.add_task(day)
            elif k == "e":
                actions.edit_task(day)
            elif k == "x":
                actions.delete_task(day)
            elif k == "d":
                actions.done_task(day)

            # habit toggle
            elif k == "h":
                actions.toggle_habit(day)

            # reflection
            elif k == "r":
                actions.reflect(day)

            elif k:
                console.print(f"  [muted]Unknown command: {k!r}[/]")
                time.sleep(0.5)

    finally:
        db.close()
        screens.farewell()
