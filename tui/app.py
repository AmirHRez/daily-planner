import os
import time
from datetime import date, timedelta
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from config import THEME
from database import DatabaseManager
from tui.helpers import day_mode, clr
from tui.actions import (
    action_add_task,
    action_delete_task,
    action_done_task,
    action_edit_task,
    action_reflect,
    action_toggle_habit,
)
from tui.screens import ScreenManager

os.makedirs("data", exist_ok=True)


console = Console(theme=THEME, highlight=False)


def main():
    db = DatabaseManager()
    current_date = date.today()
    screens = ScreenManager(console)

    try:
        while True:
            today = date.today()
            mode = day_mode(current_date)
            day = db.get_or_create_day(current_date)

            # ── render ──
            if mode == "plan":
                screens.screen_plan(day, current_date)
            elif mode == "today":
                screens.screen_today(day, current_date)
            else:
                screens.screen_reflect(day, current_date)

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
                picked = screens.screen_history_browser(db)
                if picked:
                    current_date = picked

            # task actions
            elif k == "a":
                action_add_task(db, day)
            elif k == "e":
                action_edit_task(db, day)
            elif k == "x":
                action_delete_task(db, day)
            elif k == "d":
                action_done_task(db, day)

            # habit toggle
            elif k == "h":
                action_toggle_habit(db, day)

            # reflection
            elif k == "r":
                action_reflect(db, day)

            elif k:
                console.print(f"  [muted]Unknown command: {k!r}[/]")
                time.sleep(0.5)

    finally:
        db.close()
        clr()
        console.print()
        console.print(
            Align.center(
                Panel(
                    Text(
                        "\n  Good work. See you tomorrow.  \n",
                        style="rust.bold",
                        justify="center",
                    ),
                    border_style="#C0392B",
                    padding=(1, 6),
                )
            )
        )
        console.print()
