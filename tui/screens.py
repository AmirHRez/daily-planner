from datetime import date, timedelta
from rich.align import Align
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Console
from rich import box
from rich.prompt import Prompt
from rich.rule import Rule
from typing import Optional

from tui.helpers import mode_badge
from tui.panels import panel_top3, panel_tasks, panel_habits, panel_reflection


from database import DatabaseManager


class ScreenManager:
    def __init__(self, c: Console):
        self.console = c

    def render_header(self, current_date: date, mode: str):
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
        self.console.print()
        self.console.print(
            Columns(
                [
                    Align(Text.assemble(title, rel), vertical="middle"),
                    Align(badge, vertical="middle"),
                    Align(nav, vertical="middle"),
                ],
                expand=True,
            )
        )
        self.console.print(Rule(style="#D6D3D1", characters="═"))
        self.console.print()

    def screen_plan(self, day, current_date: date):
        self.console.clear()
        self.render_header(current_date, "plan")
        self.console.print(
            Align.center(
                Text("Tonight you plan. Tomorrow you execute.", style="muted italic")
            )
        )
        self.console.print()
        self.console.print(panel_top3(day))
        self.console.print()
        self.console.print(panel_tasks(day))
        self.console.print()
        self.console.print(panel_habits(day))
        self.console.print()
        self.console.print(
            Panel(
                self._cmds(("a", "add task"), ("e", "edit task"), ("x", "del task")),
                border_style="#D6D3D1",
                padding=(0, 0),
            )
        )

    def screen_today(self, day, current_date: date):
        done_t = sum(1 for t in day.tasks if t.done)
        done_h = sum(1 for h in day.habits if h.done)
        tot_t = len(day.tasks)
        tot_h = len(day.habits)

        pct_t = int(done_t / tot_t * 100) if tot_t else 0
        pct_h = int(done_h / tot_h * 100) if tot_h else 0
        bar_t = "█" * (pct_t // 10) + "░" * (10 - pct_t // 10)
        bar_h = "█" * (pct_h // 10) + "░" * (10 - pct_h // 10)

        self.console.clear()
        self.render_header(current_date, "today")

        sg = Table.grid(expand=True, padding=(0, 3))
        sg.add_column(ratio=1)
        sg.add_column(ratio=1)
        sg.add_row(
            Text(f"Tasks   {bar_t}  {done_t}/{tot_t}", style="ink.light"),
            Text(f"Habits  {bar_h}  {done_h}/{tot_h}", style="ink.light"),
        )
        self.console.print(Panel(sg, border_style="#D6D3D1", padding=(0, 2)))
        self.console.print()
        self.console.print(panel_top3(day))
        self.console.print()
        self.console.print(panel_tasks(day))
        self.console.print()
        self.console.print(panel_habits(day))
        self.console.print()
        self.console.print(
            Panel(
                self._cmds(
                    ("d", "done task"),
                    ("h", "habit"),
                    ("a", "add task"),
                    ("r", "reflect"),
                ),
                border_style="#D6D3D1",
                padding=(0, 0),
            )
        )

    def screen_reflect(self, day, current_date: date):
        self.console.clear()
        self.render_header(current_date, "reflect")
        self.console.print(
            Columns(
                [
                    panel_tasks(day, indexed=False),
                    panel_habits(day),
                ],
                equal=True,
                expand=True,
            )
        )
        self.console.print()
        self.console.print(panel_reflection(day))
        self.console.print()
        has = any(
            [
                day.went_well,
                day.wasted_time,
                day.adjustment,
                day.sleep_hours,
                day.energy,
            ]
        )
        rlabel = "edit reflection" if has else "write reflection"
        self.console.print(
            Panel(
                self._cmds(("r", rlabel), ("d", "done task"), ("h", "habit")),
                border_style="#D6D3D1",
                padding=(0, 0),
            )
        )

    def screen_history_view(self, day, current_date: date):
        self.console.clear()
        self.render_header(current_date, "history")
        self.console.print(
            Columns(
                [
                    panel_tasks(day, indexed=False),
                    panel_habits(day),
                ],
                equal=True,
                expand=True,
            )
        )
        self.console.print()
        self.console.print(panel_reflection(day))
        self.console.print()
        self.console.print(
            Panel(
                self._cmds(
                    ("b/←", "prev day"),
                    ("n/→", "next day"),
                    ("t", "today"),
                    ("H", "browser"),
                ),
                border_style="#D6D3D1",
                padding=(0, 0),
            )
        )

    # FIXME: Remove DB logic
    def screen_history_browser(self, db: DatabaseManager) -> Optional[date]:
        self.console.clear()
        self.console.print()
        self.console.print(
            Rule("  HISTORY — last 30 days  ", style="#D6D3D1", characters="═")
        )
        self.console.print()

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

        self.console.print(Align.center(tbl))
        self.console.print()
        self.console.print(
            Align.center(
                Text(
                    "Enter a # to inspect that day, or blank to go back.", style="muted"
                )
            )
        )
        self.console.print()

        raw = Prompt.ask("  [prompt]#[/]", default="").strip()
        if not raw:
            return None
        try:
            return entries[int(raw) - 1]
        except (ValueError, IndexError):
            return None

    def _cmds(self, *pairs) -> Text:
        t = Text(justify="center")
        for key, desc in pairs:
            t.append(f"  [{key}]", style="rust")
            t.append(f" {desc}  ", style="muted")
        return t
