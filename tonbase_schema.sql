PRAGMA foreign_keys = ON;

CREATE TABLE server (
    id INTEGER PRIMARY KEY
);

CREATE TABLE allowed_roles (
    role_id INTEGER PRIMARY KEY,
    server_id INTEGER NOT NULL,
    FOREIGN KEY (server_id) REFERENCES server(id) ON DELETE CASCADE
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    time INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    recurring INTEGER,
    recurring_when INTEGER,
    description TEXT,
    image_url TEXT,
    notification_channel INTEGER,
    ping_role INTEGER NOT NULL,
    server_id INTEGER NOT NULL,
    FOREIGN KEY (server_id) REFERENCES server(id) ON DELETE CASCADE
);