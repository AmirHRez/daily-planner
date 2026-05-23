"""FIXME: Remove business logic and move to services"""

from rich.console import Console
from rich.prompt import Confirm, Prompt

from config import THEME
from tui.helpers import divider, pause


# FIXME: Use dependency injection
console = Console(theme=THEME, highlight=False)


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
