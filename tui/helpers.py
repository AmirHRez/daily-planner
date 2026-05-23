from datetime import date
from typing import Optional
from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from config import THEME, ENERGY_MAP, PRIORITY_STYLE
import constants as const

# FIXME: Use dependency injection for console
console = Console(theme=THEME, highlight=False)


def clr():
    console.clear()


def pause(msg: str = "Enter to continue…"):
    console.print()
    console.input(f"  [muted]{msg}[/]  ")


def divider(label: str = ""):
    if label:
        console.print(Rule(f"  {label}  ", style="#D6D3D1", characters="─"))
    else:
        console.print(Rule(style="#D6D3D1", characters="─"))


def mode_badge(m: str) -> Text:
    labels = {
        "plan": "  PLAN TOMORROW  ",
        "today": "  TODAY  ",
        "reflect": "  REFLECT  ",
        "history": "  HISTORY  ",
    }
    styles = {
        "plan": "mode.plan",
        "today": "mode.today",
        "reflect": "mode.reflect",
        "history": "mode.history",
    }
    return Text(labels.get(m, m.upper()), style=styles.get(m, ""))


def day_mode(d: date) -> str:
    today = date.today()
    if d > today:
        return "plan"
    elif d == today:
        return "today"
    else:
        return "history"


def energy_str(e: Optional[int]) -> str:
    return ENERGY_MAP.get(e, "—") if e else "—"


def sleep_display(h: Optional[float]) -> str:
    if h is None:
        return "—"
    filled = min(const.IDEAL_SLEEP_HOURS, int(round(h)))
    return "█" * filled + "░" * (const.IDEAL_SLEEP_HOURS - filled) + f"  {h}h"


def priority_text(p: str) -> Text:
    return Text(f"[{p.upper()}]", style=PRIORITY_STYLE.get(p.upper(), "prio.C"))
