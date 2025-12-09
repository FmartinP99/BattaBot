-- if you are using SupaBase, create the schema equivalent to this in your project.

CREATE TABLE Reminders (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    SERVER_ID TEXT NOT NULL,
    CHANNEL_ID TEXT NOT NULL,
    USER_ID TEXT NOT NULL,
    CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP, -- auto-calculated when inserting
    REMIND_TIME DATETIME,
    REMIND_TEXT TEXT,
    REMIND_HAPPENED INTEGER DEFAULT 0 CHECK (REMIND_HAPPENED IN (0, 1))  -- 0 = False, 1 = True  supposed to be bool but sqlite3 does not support bool
);