from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Habit:
    id: int
    name: str
    active: bool


@dataclass
class HabitLogEntry:
    id: int
    day_id: int
    habit_id: int
    habit_name: str
    done: bool


@dataclass
class Task:
    id: int
    day_id: int
    text: str
    priority: str  # single letter A-Z
    effort: Optional[float]
    is_top3: bool
    is_deep: bool
    done: bool


@dataclass
class Day:
    id: int
    date: date
    sleep_hours: Optional[float]
    energy: Optional[int]
    went_well: Optional[str]
    wasted_time: Optional[str]
    adjustment: Optional[str]
    tasks: list[Task] = field(default_factory=list)
    habits: list[HabitLogEntry] = field(default_factory=list)
