import sqlite3
from pathlib import Path
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple


class DailyPlannerDB:
    """Complete CRUD operations for Daily Planner"""

    def __init__(self, db_path: str = "data/planner.db"):
        """Initialize database connection and create tables if not exist"""
        Path("data").mkdir(exist_ok=True)
        self.db_path = Path("data") / Path(db_path).name
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory for dict-like rows"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Activates foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_tables(self) -> None:
        """Create all tables with proper schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tables
            cursor.executescript("""
                CREATE TABLE days (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,

                    sleep_hours REAL,
                    energy INTEGER,

                    went_well TEXT,
                    wasted_time TEXT,
                    adjustment TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day_id INTEGER NOT NULL,

                    title TEXT NOT NULL,
                    priority TEXT,
                    effort_hours REAL,

                    deep_work INTEGER DEFAULT 0,
                    done INTEGER DEFAULT 0,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY(day_id) REFERENCES days(id)
                );

                CREATE TABLE habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    active INTEGER DEFAULT 1,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE habit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    day_id INTEGER NOT NULL,
                    habit_definition_id INTEGER NOT NULL,

                    done INTEGER DEFAULT 0,

                    FOREIGN KEY(day_id) REFERENCES days(id),
                    FOREIGN KEY(habit_definition_id)
                        REFERENCES habit_definitions(id)
                );
            """)

            # TODO: Create indexes for performance

            conn.commit()

    #### Day CRUD ####
    # CREATE
    def create_day(
        self,
        date_str: str,
        sleep_hours: Optional[float] = None,
        energy: Optional[int] = None,
        wasted_time: str = "",
        went_well: str = "",
        adjustment: str = "",
    ) -> int:
        """
        Create a new daily plan (day) entry.
        Returns the ID of the created record.
        """
        if energy is not None and not (1 <= energy <= 10):
            raise ValueError("Energy must be between 1 and 10")
        if sleep_hours is not None and not (0 <= sleep_hours <= 24):
            raise ValueError("Sleep hours must be between 0 and 24")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO daily_plan (date, sleep_hours, energy, went_well, wasted_time, adjustment)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (date_str, sleep_hours, energy, went_well, wasted_time, adjustment),
            )
            conn.commit()
            return cursor.lastrowid

    # READ
    def get_day(self, date_str: str) -> Optional[Dict[str, Any]]:
        """Get a daily plan by date. Returns None if not found"""

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM days WHERE date = ?
            """,
                (date_str),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_day_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Get a daily plan by id. Returns None if not found"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM day WHERE id = ?
            """,
                (id),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # UPDATE
    def update_day(
        self,
        date_str: str,
        sleep_hours: Optional[float] = None,
        energy: Optional[int] = None,
        wasted_time: str = "",
        went_well: str = "",
        adjustment: str = "",
    ) -> bool:
        """Upadate a day's plan by date"""

        if sleep_hours is not None and not (0 <= sleep_hours <= 24):
            raise ValueError("Sleep hours must be between 0 and 24")
        if sleep_hours is not None and not (0 <= sleep_hours <= 24):
            raise ValueError("Sleep hours must be between 0 and 24")

        updates = []
        params = []
        if sleep_hours is not None:
            updates.append("sleep_hours")
            params.append(sleep_hours)

        if energy is not None:
            updates.append("enerhy")
            params.append(energy)

        if wasted_time is not None:
            updates.append("wasted_time")
            params.append(wasted_time)

        if adjustment is not None:
            updates.append("adjustment")
            params.append(adjustment)

        if went_well is not None:
            updates.append("went_well")
            params.append(went_well)

        if not updates:
            return True  # Nothing

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(date_str)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""UPDATE days SET {", ".join(updates)} WHERE date = ?""",
                (params),
            )
            conn.commit()
            return cursor.rowcount > 0

    # DELETE
    def delete_day(self, date_str: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""DELETE FROM days WHERE date = ?""", date_str)

            conn.commit()

    #### Tasks ####
    # TODO: CREATE
    # TODO: READ
    # TODO: UPDATE
    # TODO: DELETE

    #### Habits ####
    # TODO: CREATE
    # TODO: READ
    # TODO: UPDATE
    # TODO: DELETE

    @staticmethod
    def _get_day_name(date_str: str) -> str:
        """Convert YYYY-MM-DD to day name (e.g., 'Monday')."""
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return d.strftime("%A")
        except ValueError:
            return ""
