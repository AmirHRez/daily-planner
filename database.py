import sqlite3
from datetime import date
from typing import Optional
from models import Day, Habit, HabitLogEntry, Task


class DatabaseManager:
    def __init__(self, db_path: str = "data/planner.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def _init_db(self):
        with open("schema.sql") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_or_create_day(self, target_date: date) -> Day:
        row = self.conn.execute(
            "SELECT * FROM days WHERE date = ?", (target_date.isoformat(),)
        ).fetchone()

        if row is None:  # create
            self.conn.execute(
                "INSERT INTO days (date) VALUES (?)", (target_date.isoformat(),)
            )

            # seed habit log
            day_id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            habits = self.conn.execute(
                "SELECT id FROM habits WHERE active = 1"
            ).fetchall()
            self.conn.executemany(
                "INSERT OR IGNORE INTO habit_log (day_id, habit_id) VALUES (?, ?)",
                [(day_id, h["id"]) for h in habits],
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT * FROM days WHERE id = ?", (day_id,)
            ).fetchone()

        day = Day(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            sleep_hours=row["sleep_hours"],
            energy=row["energy"],
            went_well=row["went_well"],
            wasted_time=row["wasted_time"],
            adjustment=row["adjustment"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        day.tasks = self.get_tasks(day.id)
        day.habits = self.get_habit_log(day.id)
        return day

    def update_day(self, day_id: int, **kwargs):
        allowed = {"sleep_hours", "energy", "went_well", "wasted_time", "adjustment"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        set_clause += ", updated_at = CURRENT_TIMESTAMP"

        self.conn.execute(
            f"UPDATE days SET {set_clause} WHERE id = ?", (*fields.values(), day_id)
        )
        self.conn.commit()

    def get_tasks(self, day_id: int) -> list[Task]:
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE day_id = ? ORDER BY priority, id", (day_id,)
        ).fetchall()
        return [
            Task(
                id=row["id"],
                day_id=row["day_id"],
                text=row["text"],
                priority=row["priority"],
                effort=row["effort"],
                is_deep=bool(row["is_deep"]),
                done=bool(row["done"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def add_task(
        self,
        day_id: int,
        text: str,
        priority: str = "C",
        effort: Optional[float] = None,
        is_deep: bool = False,
    ) -> Task:
        cur = self.conn.execute(
            "INSERT INTO tasks (day_id, text, priority, effort, is_deep) VALUES (?, ?, ?, ?, ?)",
            (day_id, text, priority.upper(), effort, int(is_deep)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return Task(
            id=row["id"],
            day_id=row["day_id"],
            text=row["text"],
            priority=row["priority"],
            effort=row["effort"],
            is_deep=bool(row["is_deep"]),
            done=bool(row["done"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_task(self, task_id: int, **kwargs):
        allowed = {"text", "priority", "effort", "is_deep", "done"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        set_clause += ", updated_at = CURRENT_TIMESTAMP"

        self.conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?", (*fields.values(), task_id)
        )
        self.conn.commit()

    def delete_task(self, task_id: int):
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def get_habits(self) -> list[Habit]:
        rows = self.conn.execute("SELECT * FROM habits ORDER BY id").fetchall()
        return [
            Habit(id=r["id"], name=r["name"], active=bool(r["active"])) for r in rows
        ]

    def add_habit(self, name: str) -> Habit:
        cur = self.conn.execute("INSERT INTO habits (name) VALUES (?)", (name,))
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM habits WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return Habit(id=row["id"], name=row["name"], active=bool(row["active"]))

    def set_habit_active(self, habit_id: int, active: bool):
        self.conn.execute(
            "UPDATE habits SET active = ? WHERE id = ?", (int(active), habit_id)
        )
        self.conn.commit()

    def get_habit_log(self, day_id: int) -> list[HabitLogEntry]:
        rows = self.conn.execute(
            """SELECT hl.*, h.name AS habit_name FROM habit_log hl
               JOIN habits h ON h.id = hl.habit_id
               WHERE hl.day_id = ? ORDER BY h.id""",
            (day_id,),
        ).fetchall()
        return [
            HabitLogEntry(
                id=r["id"],
                day_id=r["day_id"],
                habit_id=r["habit_id"],
                habit_name=r["habit_name"],
                done=bool(r["done"]),
            )
            for r in rows
        ]

    def toggle_habit(self, day_id: int, habit_id: int) -> bool:
        row = self.conn.execute(
            "SELECT done FROM habit_log WHERE day_id = ? AND habit_id = ?",
            (day_id, habit_id),
        ).fetchone()
        new_state = not bool(row["done"])
        self.conn.execute(
            "UPDATE habit_log SET done = ? WHERE day_id = ? AND habit_id = ?",
            (int(new_state), day_id, habit_id),
        )
        self.conn.commit()
        return new_state
