from rich.theme import Theme

THEME = Theme(
    {
        "ink": "#1C1917",
        "ink.light": "#78716C",
        "ink.faint": "#A8A29E",
        "rust": "#C0392B",
        "rust.bold": "bold #C0392B",
        "gold": "#B7791F",
        "done": "strike #A8A29E",
        "undone": "#5F5B59",
        "prio.A": "bold #C0392B",
        "prio.B": "bold #B7791F",
        "prio.C": "#44403C",
        "habit.yes": "#166534",
        "habit.no": "#A8A29E",
        "success": "#166534",
        "danger": "#C0392B",
        "border": "#D6D3D1",
        "section": "bold #78716C",
        "title.top3": "bold #C0392B",  # panel title: TOP 3
        "title.tasks": "bold #78716C",  # panel title: TASKS
        "title.habits": "bold #78716C",
        "title.reflect": "bold #78716C",
        "muted": "#A8A29E",
        "prompt": "bold #1C1917",
        "mode.plan": "bold white on #1C1917",
        "mode.today": "bold white on #166534",
        "mode.reflect": "bold #1C1917 on #B7791F",
        "mode.history": "bold #1C1917 on #A8A29E",
    }
)

PRIORITY_STYLE = {"A": "prio.A", "B": "prio.B", "C": "prio.C"}

ENERGY_MAP = {
    1: "▂▁▁▁▁  1 drained",
    2: "▄▄▁▁▁  2 low",
    3: "▆▆▆▁▁  3 decent",
    4: "█▆▆▆▁  4 good",
    5: "█████  5 peak",
}
