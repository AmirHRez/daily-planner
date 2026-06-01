import json
from pathlib import Path
from database import DatabaseManager
from datetime import date
from constants import EXPORT_PATH


class IOService:
    def __init__(self, db: DatabaseManager):
        self._db = db

    def export_json(
        self, out_path: Path = Path(EXPORT_PATH) / "daily-planner-data.json"
    ) -> Path:
        """Export the full database in JSON format for analysis"""

        out_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._db.conn

        days = conn.execute("SELECT * FROM days ORDER BY date").fetchall()
        data = []

        for day in days:
            day_id = day["id"]

            tasks = conn.execute(
                "SELECT text, priority, effort, is_deep, done FROM tasks WHERE day_id = ? ORDER BY priority, id",
                (day_id,),
            ).fetchall()

            habits = conn.execute(
                """SELECT h.name, hl.done FROM habit_log hl
                JOIN habits h ON h.id = hl.habit_id
                WHERE hl.day_id = ? ORDER BY h.id""",
                (day_id,),
            ).fetchall()

            data.append(
                {
                    "date": day["date"],
                    "sleep_hours": day["sleep_hours"],
                    "energy": day["energy"],
                    "went_well": day["went_well"],
                    "wasted_time": day["wasted_time"],
                    "adjustment": day["adjustment"],
                    "tasks": [
                        {
                            "text": t["text"],
                            "priority": t["priority"],
                            "effort_hours": t["effort"],
                            "is_deep": bool(t["is_deep"]),
                            "done": bool(t["done"]),
                        }
                        for t in tasks
                    ],
                    "habits": {h["name"]: bool(h["done"]) for h in habits},
                }
            )

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return out_path

    def backup_json(self, out_path: Path = Path(EXPORT_PATH) / "backup.json") -> Path:
        """Export full database in JSON format for backup"""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._db.conn
        data = {
            "exported_at": date.today().isoformat(),
            "habits": [
                dict(r) for r in conn.execute("SELECT * FROM habits").fetchall()
            ],
            "days": [dict(r) for r in conn.execute("SELECT * FROM days").fetchall()],
            "tasks": [dict(r) for r in conn.execute("SELECT * FROM tasks").fetchall()],
            "habit_log": [
                dict(r) for r in conn.execute("SELECT * FROM habit_log").fetchall()
            ],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return out_path

    def restore_json(
        self, backup_path: Path = Path(EXPORT_PATH) / "backup.json"
    ) -> None:
        """Import a previously exported JSON that replaces current database"""
        with open(backup_path, encoding="utf-8") as f:
            data = json.load(f)

        conn = self._db.conn
        conn.execute("DELETE FROM habit_log")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM days")
        conn.execute("DELETE FROM habits")

        conn.executemany(
            "INSERT INTO habits (id, name, active) VALUES (:id, :name, :active)",
            data.get("habits", []),
        )
        conn.executemany(
            """INSERT INTO days (id, date, sleep_hours, energy, went_well, wasted_time,
               adjustment, created_at, updated_at)
               VALUES (:id, :date, :sleep_hours, :energy, :went_well, :wasted_time,
               :adjustment, :created_at, :updated_at)""",
            data.get("days", []),
        )
        conn.executemany(
            """INSERT INTO tasks (id, day_id, text, priority, effort, is_deep, done,
               created_at, updated_at)
               VALUES (:id, :day_id, :text, :priority, :effort, :is_deep, :done,
               :created_at, :updated_at)""",
            data.get("tasks", []),
        )
        conn.executemany(
            "INSERT INTO habit_log (id, day_id, habit_id, done) VALUES (:id, :day_id, :habit_id, :done)",
            data.get("habit_log", []),
        )
        conn.commit()
