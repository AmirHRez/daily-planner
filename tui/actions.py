from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from models import Day
from planner_services import PlannerService


class ActionHandler:
    def __init__(self, console: Console, service: PlannerService):
        self._c = console
        self._svc = service

    def _divider(self, label: str = "") -> None:
        if label:
            self._c.print(Rule(f"  {label}  ", style="#D6D3D1", characters="─"))
        else:
            self._c.print(Rule(style="#D6D3D1", characters="─"))

    def _pause(self, msg: str = "Enter to continue…") -> None:
        self._c.print()
        self._c.input(f"  [muted]{msg}[/]  ")

    # Tasks
    def add_task(self, day: Day) -> None:
        self._c.print()
        self._divider("ADD TASK")
        text = Prompt.ask("  [prompt]Description[/]").strip()
        if not text:
            return
        self._c.print("  [muted]Priority: A critical · B important · C normal[/]")
        priority = Prompt.ask(
            "  [prompt]Priority[/]", default="C", choices=["A", "B", "C"]
        ).upper()
        effort_s = Prompt.ask(
            "  [prompt]Effort hours (blank skip)[/]", default=""
        ).strip()
        effort = float(effort_s) if effort_s else None
        is_deep = Confirm.ask("  [prompt]Deep work?[/]", default=False)
        self._svc.add_task(
            day.id, text, priority=priority, effort=effort, is_deep=is_deep
        )
        self._c.print("  [success]✓ Task added.[/]")
        self._pause()

    def edit_task(self, day: Day) -> None:
        if not day.tasks:
            self._c.print("  [muted]No tasks.[/]")
            self._pause()
            return
        self._c.print()
        self._divider("EDIT TASK")
        for i, t in enumerate(day.tasks, 1):
            self._c.print(f"  [muted]{i}.[/]  {t.text}  [muted][{t.priority}][/]")
        raw = Prompt.ask(
            "  [prompt]Task #[/] [muted](blank cancel)[/]", default=""
        ).strip()
        if not raw:
            return
        try:
            task = day.tasks[int(raw) - 1]
        except (ValueError, IndexError):
            self._c.print("  [danger]Invalid.[/]")
            self._pause()
            return
        text = (
            Prompt.ask("  [prompt]Description[/]", default=task.text).strip()
            or task.text
        )
        priority = Prompt.ask(
            "  [prompt]Priority[/]", default=task.priority, choices=["A", "B", "C"]
        ).upper()
        effort_s = Prompt.ask(
            "  [prompt]Effort hrs[/]", default=str(task.effort) if task.effort else ""
        ).strip()
        effort = float(effort_s) if effort_s else None
        is_deep = Confirm.ask("  [prompt]Deep work?[/]", default=task.is_deep)
        self._svc.edit_task(
            task.id, text=text, priority=priority, effort=effort, is_deep=is_deep
        )
        self._c.print("  [success]✓ Updated.[/]")
        self._pause()

    def toggle_done(self, day: Day) -> None:
        if not day.tasks:
            self._c.print("  [muted]No tasks.[/]")
            self._pause()
            return
        self._c.print()
        self._divider("MARK DONE / UNDONE")
        for i, t in enumerate(day.tasks, 1):
            mark = "[success]✓[/]" if t.done else "[muted]☐[/]"
            self._c.print(f"  {mark}  [muted]{i}.[/]  {t.text}")
        raw = Prompt.ask(
            "  [prompt]Task #[/] [muted](blank cancel)[/]", default=""
        ).strip()
        if not raw:
            return
        try:
            task = day.tasks[int(raw) - 1]
            new = self._svc.toggle_task_done(task.id, task.done)
            state = "[success]done ✓[/]" if new else "[muted]undone ☐[/]"
            self._c.print(f"  Marked {state}")
        except (ValueError, IndexError):
            self._c.print("  [danger]Invalid.[/]")
        self._pause()

    def delete_task(self, day: Day) -> None:
        if not day.tasks:
            self._c.print("  [muted]No tasks.[/]")
            self._pause()
            return
        self._c.print()
        self._divider("DELETE TASK")
        for i, t in enumerate(day.tasks, 1):
            self._c.print(f"  [muted]{i}.[/]  {t.text}")
        raw = Prompt.ask(
            "  [prompt]Task #[/] [muted](blank cancel)[/]", default=""
        ).strip()
        if not raw:
            return
        try:
            task = day.tasks[int(raw) - 1]
            if Confirm.ask(f'  [danger]Delete[/] "{task.text}"?', default=False):
                self._svc.delete_task(task.id)
                self._c.print("  [success]✓ Deleted.[/]")
        except (ValueError, IndexError):
            self._c.print("  [danger]Invalid.[/]")
        self._pause()

    # Habits
    def toggle_habit(self, day: Day) -> None:
        if not day.habits:
            self._c.print("  [muted]No habits.[/]")
            self._pause()
            return
        self._c.print()
        self._divider("TOGGLE HABIT")
        for i, h in enumerate(day.habits, 1):
            mark = "[habit.yes]✓[/]" if h.done else "[muted]☐[/]"
            self._c.print(f"  {mark}  [muted]{i}.[/]  {h.habit_name}")
        raw = Prompt.ask(
            "  [prompt]Habit #[/] [muted](blank cancel)[/]", default=""
        ).strip()
        if not raw:
            return
        try:
            h = day.habits[int(raw) - 1]
            new = self._svc.toggle_habit(day.id, h.habit_id)
            st = "[habit.yes]done ✓[/]" if new else "[muted]undone ☐[/]"
            self._c.print(f"  {h.habit_name}  →  {st}")
        except (ValueError, IndexError):
            self._c.print("  [danger]Invalid.[/]")
        self._pause()

    # Reflection
    def reflect(self, day: Day) -> None:
        self._c.print()
        self._divider("REFLECTION")

        sleep_s = Prompt.ask(
            "  [prompt]Sleep hours[/]",
            default=str(day.sleep_hours) if day.sleep_hours else "",
        ).strip()
        sleep = float(sleep_s) if sleep_s else None

        self._c.print("  [muted]1 drained · 2 low · 3 decent · 4 good · 5 peak[/]")
        energy_s = Prompt.ask(
            "  [prompt]Energy (1–5)[/]", default=str(day.energy) if day.energy else ""
        ).strip()
        energy = max(1, min(5, int(energy_s))) if energy_s else None

        self._c.print()
        went_well = (
            Prompt.ask(
                "  [prompt]What went well?[/]", default=day.went_well or ""
            ).strip()
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
                "  [prompt]One adjustment for tomorrow?[/]",
                default=day.adjustment or "",
            ).strip()
            or None
        )

        self._svc.update_reflection(day.id, sleep, energy, went_well, wasted, adjust)
        self._c.print()
        self._c.print("  [success]✓ Reflection saved.[/]")
        self._pause()
