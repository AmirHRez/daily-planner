from datetime import date, timedelta
from typing import Optional

from data.database import DatabaseManager
from models import Day, Task


class PlannerService:
    def __init__(self, db: DatabaseManager):
        self._db = db

    # Day
    def get_or_create_day(self, target_date: date) -> Day:
        return self._db.get_or_create_day(target_date)

    def day_mode(self, d: date) -> str:
        """Return 'plan', 'today', or 'history' for a given date."""
        today = date.today()
        if d > today:
            return "plan"
        elif d == today:
            return "today"
        return "history"

    def update_reflection(
        self,
        day_id: int,
        sleep_hours: Optional[float],
        energy: Optional[int],
        went_well: Optional[str],
        wasted_time: Optional[str],
        adjustment: Optional[str],
    ) -> None:
        self._db.update_day(
            day_id,
            sleep_hours=sleep_hours,
            energy=energy,
            went_well=went_well,
            wasted_time=wasted_time,
            adjustment=adjustment,
        )

    # Tasks
    def add_task(
        self,
        day_id: int,
        text: str,
        priority: str = "C",
        effort: Optional[float] = None,
        is_deep: bool = False,
    ) -> Task:
        return self._db.add_task(
            day_id, text, priority=priority, effort=effort, is_deep=is_deep
        )

    def edit_task(
        self,
        task_id: int,
        text: str,
        priority: str,
        effort: Optional[float],
        is_deep: bool,
    ) -> None:
        self._db.update_task(
            task_id,
            text=text,
            priority=priority,
            effort=effort,
            is_deep=int(is_deep),
        )

    def toggle_task_done(self, task_id: int, current_done: bool) -> bool:
        new_state = not current_done
        self._db.update_task(task_id, done=int(new_state))
        return new_state

    def delete_task(self, task_id: int) -> None:
        self._db.delete_task(task_id)

    def top3_tasks(self, day: Day) -> list[Task]:
        """Return up to 3 priority-A tasks in insertion order."""
        return sorted([t for t in day.tasks if t.priority == "A"], key=lambda t: t.id)[
            :3
        ]

    # ── Habits ────────────────────────────────────────────────────────────────

    def toggle_habit(self, day_id: int, habit_id: int) -> bool:
        return self._db.toggle_habit(day_id, habit_id)

    # ── Stats / aggregates ────────────────────────────────────────────────────

    def day_stats(self, day: Day) -> dict:
        """Quick completion counts used by progress bars and history table."""
        done_tasks = sum(1 for t in day.tasks if t.done)
        done_habits = sum(1 for h in day.habits if h.done)
        total_tasks = len(day.tasks)
        total_habits = len(day.habits)
        has_reflection = any(
            [
                day.went_well,
                day.wasted_time,
                day.adjustment,
                day.sleep_hours,
                day.energy,
            ]
        )
        return {
            "done_tasks": done_tasks,
            "total_tasks": total_tasks,
            "done_habits": done_habits,
            "total_habits": total_habits,
            "pct_tasks": int(done_tasks / total_tasks * 100) if total_tasks else 0,
            "pct_habits": int(done_habits / total_habits * 100) if total_habits else 0,
            "has_reflection": has_reflection,
        }

    def recent_days(self, n: int = 30) -> list[tuple[date, Day]]:
        """Return (date, Day) pairs for the last *n* days, newest first."""
        today = date.today()
        result = []
        for i in range(n):
            d = today - timedelta(days=i)
            result.append((d, self._db.get_or_create_day(d)))
        return result
