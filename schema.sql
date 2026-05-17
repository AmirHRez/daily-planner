CREATE TABLE IF NOT EXISTS habits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE,
    active     INTEGER NOT NULL DEFAULT 1
);

INSERT OR IGNORE INTO habits (name) VALUES
    ('English Practice'),
    ('Gym / Movement'),
    ('AI / ML Learning'),
    ('Guitar Practice'),
    ('University Study');

CREATE TABLE IF NOT EXISTS days (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL UNIQUE,
    sleep_hours REAL,
    energy      INTEGER,                  
    went_well   TEXT,
    wasted_time TEXT,
    adjustment  TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id     INTEGER NOT NULL REFERENCES days(id) ON DELETE CASCADE,
    text       TEXT    NOT NULL,
    priority   TEXT    NOT NULL DEFAULT 'C',
    effort     REAL,
    is_deep    INTEGER NOT NULL DEFAULT 0,
    done       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS habit_log (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id   INTEGER NOT NULL REFERENCES days(id)   ON DELETE CASCADE,
    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    done     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (day_id, habit_id)
);