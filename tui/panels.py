from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from tui.helpers import priority_text, energy_str, sleep_display


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
