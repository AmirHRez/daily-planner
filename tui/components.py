from datetime import date
from typing import Optional
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from models import Day
from tui.config import ENERGY_MAP, PRIORITY_STYLE
from constants import IDEAL_SLEEP_HOURS


def energy_str(e: Optional[int]) -> str:
    return ENERGY_MAP.get(e, "—") if e else "—"


def sleep_display(h: Optional[float]) -> str:
    if h is None:
        return "—"
    filled = min(IDEAL_SLEEP_HOURS, int(round(h)))
    return "█" * filled + "░" * (IDEAL_SLEEP_HOURS - filled) + f"  {h}h"


def priority_text(p: str) -> Text:
    return Text(f"[{p.upper()}]", style=PRIORITY_STYLE.get(p.upper(), "prio.C"))


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


def cmds(*pairs) -> Text:
    """Build a centred key-hint bar: [key] desc  [key] desc …"""
    t = Text(justify="center")
    for key, desc in pairs:
        t.append(f"  [{key}]", style="rust")
        t.append(f" {desc}  ", style="muted")
    return t


# Panels


def panel_top3(top3_tasks) -> Panel:
    rows = []
    for i in range(3):
        num = Text(f"  {i + 1}. ", style="rust")
        if i < len(top3_tasks):
            t = top3_tasks[i]
            label = Text(t.text, style="done" if t.done else "bold")
        else:
            label = Text("·" * 44, style="ink.faint")
        rows.append(Text.assemble(num, label))
    content = Text("\n").join(rows)
    return Panel(
        content,
        title=Text("  TOP 3 CRITICAL TASKS  ", style="title.top3"),
        border_style="#C0392B",
        padding=(1, 2),
    )


def panel_tasks(day: Day, indexed: bool = True) -> Panel:
    tbl = Table(
        box=None, show_header=True, header_style="section", expand=True, padding=(0, 1)
    )
    if indexed:
        tbl.add_column("#", style="muted", width=3, no_wrap=True)
    tbl.add_column("P", width=4, no_wrap=True)
    tbl.add_column("Task", ratio=1)
    tbl.add_column("Deep", width=5, no_wrap=True, justify="center")
    tbl.add_column("Hrs", width=5, no_wrap=True, justify="right")
    tbl.add_column("✓", width=3, no_wrap=True, justify="center")

    if not day.tasks:
        empty = Text("  No tasks yet.", style="muted")
        row = ([""] if indexed else []) + ["", empty, "", "", ""]
        tbl.add_row(*row)
    else:
        for i, task in enumerate(day.tasks, 1):
            deep = (
                Text("◆", style="ink.light")
                if task.is_deep
                else Text("·", style="muted")
            )
            check = (
                Text("✓", style="success") if task.done else Text("☐", style="muted")
            )
            eff = Text(f"{task.effort}h" if task.effort else "—", style="muted")
            txt = Text(task.text, style="done" if task.done else "undone")
            row = [Text(str(i), style="muted")] if indexed else []
            row += [priority_text(task.priority), txt, deep, eff, check]
            tbl.add_row(*row)

    return Panel(
        tbl,
        title=Text(f"  TASKS  ({len(day.tasks)})  ", style="title.tasks"),
        border_style="#D6D3D1",
        padding=(0, 0),
    )


def panel_habits(day: Day) -> Panel:
    lines = []
    if not day.habits:
        lines.append(Text("  No habits tracked.", style="muted"))
    else:
        for h in day.habits:
            mark = (
                Text("  ✓ ", style="habit.yes")
                if h.done
                else Text("  ☐ ", style="muted")
            )
            name = Text(h.habit_name, style="habit.yes" if h.done else "ink.light")
            lines.append(Text.assemble(mark, name))
    content = Text("\n").join(lines)
    return Panel(
        content,
        title=Text("  HABITS  ", style="title.habits"),
        border_style="#D6D3D1",
        padding=(1, 0),
    )


def panel_reflection(day: Day) -> Panel:
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(style="section", width=24, no_wrap=True)
    grid.add_column(ratio=1)

    def v(val, style="undone"):
        return Text(val, style=style) if val else Text("—", style="muted")

    grid.add_row("Sleep", Text(sleep_display(day.sleep_hours), style="ink.light"))
    grid.add_row("Energy", Text(energy_str(day.energy), style="ink.light"))
    grid.add_row("", Text(""))
    grid.add_row("What went well?", v(day.went_well))
    grid.add_row("What wasted time?", v(day.wasted_time))
    grid.add_row("Adjustment tomorrow?", v(day.adjustment))

    return Panel(
        grid,
        title=Text("  REFLECTION  ", style="title.reflect"),
        border_style="#D6D3D1",
        padding=(1, 2),
    )


# Header
def render_header(console: Console, current_date: date, mode: str) -> None:
    today = date.today()
    badge = mode_badge(mode)
    title = Text.assemble(
        Text("DAILY PLANNER", style="bold"),
        Text("   ·   ", style="muted"),
        Text(current_date.strftime("%A").upper(), style="rust"),
        Text("  ", style=""),
        Text(current_date.strftime("%d %B %Y"), style="ink.light"),
    )
    delta = (current_date - today).days
    if delta == 0:
        rel = Text("  today", style="gold")
    elif delta == 1:
        rel = Text("  tomorrow", style="muted")
    elif delta == -1:
        rel = Text("  yesterday", style="muted")
    else:
        rel = Text(f"  {delta:+}d", style="muted")

    nav = Text("b/← prev   n/→ next   t today   H history   q quit", style="muted")
    console.print()
    console.print(
        Columns(
            [
                Align(Text.assemble(title, rel), vertical="middle"),
                Align(badge, vertical="middle"),
                Align(nav, vertical="middle"),
            ],
            expand=True,
        )
    )
    console.print(Rule(style="#D6D3D1", characters="═"))
    console.print()
