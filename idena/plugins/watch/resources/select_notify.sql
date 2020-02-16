SELECT users.ntfy_telegram, users.ntfy_email, users.ntfy_discord
FROM users
LEFT JOIN nodes ON nodes.user_id = users.user_id
WHERE nodes.address = ?