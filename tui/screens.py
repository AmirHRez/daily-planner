from datetime import date
from typing import Optional
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from models import Day
from planner_services import PlannerService
from tui.components import (
    cmds,
    panel_habits,
    panel_reflection,
    panel_tasks,
    panel_top3,
    render_header,
)


class ScreenManager:
    def __init__(self, console: Console, service: PlannerService):
        self._c = console
        self._svc = service

    def _clr(self):
        self._c.clear()

    def _cmd_bar(self, *pairs) -> None:
        self._c.print(Panel(cmds(*pairs), border_style="#D6D3D1", padding=(0, 0)))

    # Screens
    def plan(self, day: Day, current_date: date) -> None:
        self._clr()
        render_header(self._c, current_date, "plan")
        self._c.print(
            Align.center(
                Text("Tonight you plan. Tomorrow you execute.", style="muted italic")
            )
        )
        self._c.print()
        self._c.print(panel_top3(self._svc.top3_tasks(day)))
        self._c.print()
        self._c.print(panel_tasks(day))
        self._c.print()
        self._c.print(panel_habits(day))
        self._c.print()
        self._cmd_bar(("a", "add task"), ("e", "edit task"), ("x", "del task"))

    def today(self, day: Day, current_date: date) -> None:
        stats = self._svc.day_stats(day)
        pct_t, pct_h = stats["pct_tasks"], stats["pct_habits"]
        done_t, tot_t = stats["done_tasks"], stats["total_tasks"]
        done_h, tot_h = stats["done_habits"], stats["total_habits"]

        bar_t = "█" * (pct_t // 10) + "░" * (10 - pct_t // 10)
        bar_h = "█" * (pct_h // 10) + "░" * (10 - pct_h // 10)

        self._clr()
        render_header(self._c, current_date, "today")

        sg = Table.grid(expand=True, padding=(0, 3))
        sg.add_column(ratio=1)
        sg.add_column(ratio=1)
        sg.add_row(
            Text(f"Tasks   {bar_t}  {done_t}/{tot_t}", style="ink.light"),
            Text(f"Habits  {bar_h}  {done_h}/{tot_h}", style="ink.light"),
        )
        self._c.print(Panel(sg, border_style="#D6D3D1", padding=(0, 2)))
        self._c.print()
        self._c.print(panel_top3(self._svc.top3_tasks(day)))
        self._c.print()
        self._c.print(panel_tasks(day))
        self._c.print()
        self._c.print(panel_habits(day))
        self._c.print()
        self._cmd_bar(
            ("d", "done task"), ("h", "habit"), ("a", "add task"), ("r", "reflect")
        )

    def reflect(self, day: Day, current_date: date) -> None:
        self._clr()
        render_header(self._c, current_date, "reflect")
        self._c.print(
            Columns(
                [panel_tasks(day, indexed=False), panel_habits(day)],
                equal=True,
                expand=True,
            )
        )
        self._c.print()
        self._c.print(panel_reflection(day))
        self._c.print()
        has = self._svc.day_stats(day)["has_reflection"]
        self._cmd_bar(
            ("r", "edit reflection" if has else "write reflection"),
            ("d", "done task"),
            ("h", "habit"),
        )

    def history_view(self, day: Day, current_date: date) -> None:
        self._clr()
        render_header(self._c, current_date, "history")
        self._c.print(
            Columns(
                [panel_tasks(day, indexed=False), panel_habits(day)],
                equal=True,
                expand=True,
            )
        )
        self._c.print()
        self._c.print(panel_reflection(day))
        self._c.print()
        self._cmd_bar(
            ("b/←", "prev day"), ("n/→", "next day"), ("t", "today"), ("H", "browser")
        )

    def history_browser(self) -> Optional[date]:
        self._clr()
        self._c.print()
        self._c.print(
            Rule("  HISTORY — last 30 days  ", style="#D6D3D1", characters="═")
        )
        self._c.print()

        from rich.prompt import Prompt

        today = date.today()
        entries = self._svc.recent_days(30)

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

        for i, (d, day) in enumerate(entries, 1):
            stats = self._svc.day_stats(day)
            date_text = Text(
                d.strftime("%d %b %Y") + ("  ← today" if d == today else ""),
                style="rust.bold" if d == today else "ink",
            )
            tbl.add_row(
                str(i),
                date_text,
                d.strftime("%a").upper(),
                f"{stats['done_tasks']}/{stats['total_tasks']}",
                f"{stats['done_habits']}/{stats['total_habits']}",
                f"{day.sleep_hours}h" if day.sleep_hours else "—",
                f"{day.energy}/5" if day.energy else "—",
                Text("✓", style="success")
                if stats["has_reflection"]
                else Text("·", style="muted"),
            )

        self._c.print(Align.center(tbl))
        self._c.print()
        self._c.print(
            Align.center(
                Text(
                    "Enter a # to inspect that day, or blank to go back.", style="muted"
                )
            )
        )
        self._c.print()

        raw = Prompt.ask("  [prompt]#[/]", default="").strip()
        if not raw:
            return None
        try:
            return entries[int(raw) - 1][0]
        except (ValueError, IndexError):
            return None

    def farewell(self) -> None:
        self._clr()
        self._c.print()
        self._c.print(
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
        self._c.print()
