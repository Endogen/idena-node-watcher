CREATE TABLE users (
	user_id TEXT NOT NULL,
	first_name TEXT NOT NULL,
	last_name TEXT,
	username TEXT,
	language TEXT,
	ntfy_telegram TEXT,
	ntfy_email TEXT,
	ntfy_discord TEXT,
	date_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (user_id)
)