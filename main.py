import os
import time
from datetime import date, timedelta
from typing import Optional

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from config import THEME, ENERGY_MAP, PRIORITY_STYLE
from database import DatabaseManager


## NOTE: AI GENERATED

os.makedirs("data", exist_ok=True)


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
    filled = min(10, int(round(h)))
    return "█" * filled + "░" * (10 - filled) + f"  {h}h"


def priority_text(p: str) -> Text:
    return Text(f"[{p.upper()}]", style=PRIORITY_STYLE.get(p.upper(), "prio.C"))


# ─────────────────────────────────────────────
#  PANELS
# ─────────────────────────────────────────────


def panel_top3(day) -> Panel:
    top3 = sorted([t for t in day.tasks if t.priority == "A"], key=lambda t: t.id)[:3]
    rows = []
    for i in range(3):
        num = Text(f"  {i + 1}. ", style="rust")
        if i < len(top3):
            t = top3[i]
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


def panel_tasks(day, indexed: bool = True) -> Panel:
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


def panel_habits(day) -> Panel:
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


def panel_reflection(day) -> Panel:
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


def render_header(current_date: date, mode: str):
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


# ─────────────────────────────────────────────
#  FOUR SCREENS
# ─────────────────────────────────────────────


def screen_plan(day, current_date: date):
    clr()
    render_header(current_date, "plan")
    console.print(
        Align.center(
            Text("Tonight you plan. Tomorrow you execute.", style="muted italic")
        )
    )
    console.print()
    console.print(panel_top3(day))
    console.print()
    console.print(panel_tasks(day))
    console.print()
    console.print(panel_habits(day))
    console.print()
    console.print(
        Panel(
            _cmds(("a", "add task"), ("e", "edit task"), ("x", "del task")),
            border_style="#D6D3D1",
            padding=(0, 0),
        )
    )


def screen_today(day, current_date: date):
    today = date.today()
    done_t = sum(1 for t in day.tasks if t.done)
    done_h = sum(1 for h in day.habits if h.done)
    tot_t = len(day.tasks)
    tot_h = len(day.habits)

    pct_t = int(done_t / tot_t * 100) if tot_t else 0
    pct_h = int(done_h / tot_h * 100) if tot_h else 0
    bar_t = "█" * (pct_t // 10) + "░" * (10 - pct_t // 10)
    bar_h = "█" * (pct_h // 10) + "░" * (10 - pct_h // 10)

    clr()
    render_header(current_date, "today")

    sg = Table.grid(expand=True, padding=(0, 3))
    sg.add_column(ratio=1)
    sg.add_column(ratio=1)
    sg.add_row(
        Text(f"Tasks   {bar_t}  {done_t}/{tot_t}", style="ink.light"),
        Text(f"Habits  {bar_h}  {done_h}/{tot_h}", style="ink.light"),
    )
    console.print(Panel(sg, border_style="#D6D3D1", padding=(0, 2)))
    console.print()
    console.print(panel_top3(day))
    console.print()
    console.print(panel_tasks(day))
    console.print()
    console.print(panel_habits(day))
    console.print()
    console.print(
        Panel(
            _cmds(
                ("d", "done task"), ("h", "habit"), ("a", "add task"), ("r", "reflect")
            ),
            border_style="#D6D3D1",
            padding=(0, 0),
        )
    )


def screen_reflect(day, current_date: date):
    clr()
    render_header(current_date, "reflect")
    console.print(
        Columns(
            [
                panel_tasks(day, indexed=False),
                panel_habits(day),
            ],
            equal=True,
            expand=True,
        )
    )
    console.print()
    console.print(panel_reflection(day))
    console.print()
    has = any(
        [day.went_well, day.wasted_time, day.adjustment, day.sleep_hours, day.energy]
    )
    rlabel = "edit reflection" if has else "write reflection"
    console.print(
        Panel(
            _cmds(("r", rlabel), ("d", "done task"), ("h", "habit")),
            border_style="#D6D3D1",
            padding=(0, 0),
        )
    )


def screen_history_view(day, current_date: date):
    clr()
    render_header(current_date, "history")
    console.print(
        Columns(
            [
                panel_tasks(day, indexed=False),
                panel_habits(day),
            ],
            equal=True,
            expand=True,
        )
    )
    console.print()
    console.print(panel_reflection(day))
    console.print()
    console.print(
        Panel(
            _cmds(
                ("b/←", "prev day"),
                ("n/→", "next day"),
                ("t", "today"),
                ("H", "browser"),
            ),
            border_style="#D6D3D1",
            padding=(0, 0),
        )
    )


def _cmds(*pairs) -> Text:
    t = Text(justify="center")
    for key, desc in pairs:
        t.append(f"  [{key}]", style="rust")
        t.append(f" {desc}  ", style="muted")
    return t


# ─────────────────────────────────────────────
#  HISTORY BROWSER
# ─────────────────────────────────────────────


def screen_history_browser(db: DatabaseManager) -> Optional[date]:
    clr()
    console.print()
    console.print(Rule("  HISTORY — last 30 days  ", style="#D6D3D1", characters="═"))
    console.print()

    today = date.today()
    entries = [today - timedelta(days=i) for i in range(30)]

    tbl = Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="section",
        expand=False,
        padding=(0, 2),
        border_style="#D6D3D1",
    )
    tbl.add_column("#", style="muted", width=4)
    tbl.add_column("Date", width=14)
    tbl.add_column("Day", style="ink.light", width=5)
    tbl.add_column("Tasks", justify="right", width=8)
    tbl.add_column("Habits", justify="right", width=8)
    tbl.add_column("Sleep", justify="right", width=7)
    tbl.add_column("Energy", justify="right", width=8)
    tbl.add_column("Journal", justify="center", width=8)

    for i, d in enumerate(entries, 1):
        day = db.get_or_create_day(d)
        done_t = sum(1 for x in day.tasks if x.done)
        done_h = sum(1 for x in day.habits if x.done)
        tot_t = len(day.tasks)
        tot_h = len(day.habits)
        has_j = any(
            [
                day.went_well,
                day.wasted_time,
                day.adjustment,
                day.sleep_hours,
                day.energy,
            ]
        )

        date_text = Text(
            d.strftime("%d %b %Y") + ("  ← today" if d == today else ""),
            style="rust.bold" if d == today else "ink",
        )
        tbl.add_row(
            str(i),
            date_text,
            d.strftime("%a").upper(),
            f"{done_t}/{tot_t}",
            f"{done_h}/{tot_h}",
            f"{day.sleep_hours}h" if day.sleep_hours else "—",
            f"{day.energy}/5" if day.energy else "—",
            Text("✓", style="success") if has_j else Text("·", style="muted"),
        )

    console.print(Align.center(tbl))
    console.print()
    console.print(
        Align.center(
            Text("Enter a # to inspect that day, or blank to go back.", style="muted")
        )
    )
    console.print()

    raw = Prompt.ask("  [prompt]#[/]", default="").strip()
    if not raw:
        return None
    try:
        return entries[int(raw) - 1]
    except (ValueError, IndexError):
        return None


# ─────────────────────────────────────────────
#  ACTIONS
# ─────────────────────────────────────────────


def action_add_task(db, day):
    console.print()
    divider("ADD TASK")
    text = Prompt.ask("  [prompt]Description[/]").strip()
    if not text:
        return
    console.print("  [muted]Priority: A critical · B important · C normal[/]")
    priority = Prompt.ask(
        "  [prompt]Priority[/]", default="C", choices=["A", "B", "C"]
    ).upper()
    effort_s = Prompt.ask("  [prompt]Effort hours (blank skip)[/]", default="").strip()
    effort = float(effort_s) if effort_s else None
    is_deep = Confirm.ask("  [prompt]Deep work?[/]", default=False)
    db.add_task(day.id, text, priority=priority, effort=effort, is_deep=is_deep)
    console.print("  [success]✓ Task added.[/]")
    pause()


def action_edit_task(db, day):
    if not day.tasks:
        console.print("  [muted]No tasks.[/]")
        pause()
        return
    console.print()
    divider("EDIT TASK")
    for i, t in enumerate(day.tasks, 1):
        console.print(f"  [muted]{i}.[/]  {t.text}  [muted][{t.priority}][/]")
    raw = Prompt.ask("  [prompt]Task #[/] [muted](blank cancel)[/]", default="").strip()
    if not raw:
        return
    try:
        task = day.tasks[int(raw) - 1]
    except (ValueError, IndexError):
        console.print("  [danger]Invalid.[/]")
        pause()
        return
    text = (
        Prompt.ask("  [prompt]Description[/]", default=task.text).strip() or task.text
    )
    priority = Prompt.ask(
        "  [prompt]Priority[/]", default=task.priority, choices=["A", "B", "C"]
    ).upper()
    effort_s = Prompt.ask(
        "  [prompt]Effort hrs[/]", default=str(task.effort) if task.effort else ""
    ).strip()
    effort = float(effort_s) if effort_s else None
    is_deep = Confirm.ask("  [prompt]Deep work?[/]", default=task.is_deep)
    db.update_task(
        task.id, text=text, priority=priority, effort=effort, is_deep=int(is_deep)
    )
    console.print("  [success]✓ Updated.[/]")
    pause()


def action_done_task(db, day):
    if not day.tasks:
        console.print("  [muted]No tasks.[/]")
        pause()
        return
    console.print()
    divider("MARK DONE / UNDONE")
    for i, t in enumerate(day.tasks, 1):
        mark = "[success]✓[/]" if t.done else "[muted]☐[/]"
        console.print(f"  {mark}  [muted]{i}.[/]  {t.text}")
    raw = Prompt.ask("  [prompt]Task #[/] [muted](blank cancel)[/]", default="").strip()
    if not raw:
        return
    try:
        task = day.tasks[int(raw) - 1]
        new = not task.done
        db.update_task(task.id, done=int(new))
        state = "[success]done ✓[/]" if new else "[muted]undone ☐[/]"
        console.print(f"  Marked {state}")
    except (ValueError, IndexError):
        console.print("  [danger]Invalid.[/]")
    pause()


def action_delete_task(db, day):
    if not day.tasks:
        console.print("  [muted]No tasks.[/]")
        pause()
        return
    console.print()
    divider("DELETE TASK")
    for i, t in enumerate(day.tasks, 1):
        console.print(f"  [muted]{i}.[/]  {t.text}")
    raw = Prompt.ask("  [prompt]Task #[/] [muted](blank cancel)[/]", default="").strip()
    if not raw:
        return
    try:
        task = day.tasks[int(raw) - 1]
        if Confirm.ask(f'  [danger]Delete[/] "{task.text}"?', default=False):
            db.delete_task(task.id)
            console.print("  [success]✓ Deleted.[/]")
    except (ValueError, IndexError):
        console.print("  [danger]Invalid.[/]")
    pause()


def action_toggle_habit(db, day):
    if not day.habits:
        console.print("  [muted]No habits.[/]")
        pause()
        return
    console.print()
    divider("TOGGLE HABIT")
    for i, h in enumerate(day.habits, 1):
        mark = "[habit.yes]✓[/]" if h.done else "[muted]☐[/]"
        console.print(f"  {mark}  [muted]{i}.[/]  {h.habit_name}")
    raw = Prompt.ask(
        "  [prompt]Habit #[/] [muted](blank cancel)[/]", default=""
    ).strip()
    if not raw:
        return
    try:
        h = day.habits[int(raw) - 1]
        new = db.toggle_habit(day.id, h.habit_id)
        st = "[habit.yes]done ✓[/]" if new else "[muted]undone ☐[/]"
        console.print(f"  {h.habit_name}  →  {st}")
    except (ValueError, IndexError):
        console.print("  [danger]Invalid.[/]")
    pause()


def action_reflect(db, day):
    console.print()
    divider("REFLECTION")

    sleep_s = Prompt.ask(
        "  [prompt]Sleep hours[/]",
        default=str(day.sleep_hours) if day.sleep_hours else "",
    ).strip()
    sleep = float(sleep_s) if sleep_s else None

    console.print("  [muted]1 drained · 2 low · 3 decent · 4 good · 5 peak[/]")
    energy_s = Prompt.ask(
        "  [prompt]Energy (1–5)[/]", default=str(day.energy) if day.energy else ""
    ).strip()
    energy = max(1, min(5, int(energy_s))) if energy_s else None

    console.print()
    went_well = (
        Prompt.ask("  [prompt]What went well?[/]", default=day.went_well or "").strip()
        or None
    )
    wasted = (
        Prompt.ask(
            "  [prompt]What wasted time?[/]", default=day.wasted_time or ""
        ).strip()
        or None
    )
    adjust = (
        Prompt.ask(
            "  [prompt]One adjustment for tomorrow?[/]", default=day.adjustment or ""
        ).strip()
        or None
    )

    db.update_day(
        day.id,
        sleep_hours=sleep,
        energy=energy,
        went_well=went_well,
        wasted_time=wasted,
        adjustment=adjust,
    )
    console.print()
    console.print("  [success]✓ Reflection saved.[/]")
    pause()


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────


def main():
    db = DatabaseManager()
    current_date = date.today()

    try:
        while True:
            today = date.today()
            mode = day_mode(current_date)
            day = db.get_or_create_day(current_date)

            # ── render ──
            if mode == "plan":
                screen_plan(day, current_date)
            elif mode == "today":
                screen_today(day, current_date)
            else:
                screen_reflect(day, current_date)

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
                picked = screen_history_browser(db)
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


if __name__ == "__main__":
    main()
