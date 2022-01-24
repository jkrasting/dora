CREATE TABLE user (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    profile_pic TEXT NOT NULL,
    remote_addr TEXT NOT NULL,
    login_date TEXT NOT NULL
)