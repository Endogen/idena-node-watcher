CREATE TABLE nodes (
	user_id TEXT NOT NULL,
	address TEXT NOT NULL,
	date_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (user_id, address),
	FOREIGN KEY(user_id) REFERENCES users(user_id)
)