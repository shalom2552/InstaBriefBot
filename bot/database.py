import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../messages.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            channel TEXT,
            date TEXT,
            text TEXT
        )
    """)
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_message_unique ON messages(channel, message_id)
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS last_fetched (
            channel TEXT PRIMARY KEY,
            last_message_id INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            name TEXT PRIMARY KEY
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_channel_updates (
            user_id INTEGER,
            channel TEXT,
            last_message_id INTEGER,
            PRIMARY KEY (user_id, channel)
        )
    """)    
    conn.commit()
    conn.close()

def save_messages(messages):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    count = 0
    for msg in messages:
        try:
            c.execute("INSERT INTO messages (message_id, channel, date, text) VALUES (?, ?, ?, ?)",
                      (msg['id'], msg['channel'], msg['date'], msg['text']))
            count += 1
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    conn.close()
    return count

def update_last_fetched(channel, message_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO last_fetched (channel, last_message_id) VALUES (?, ?)", (channel, message_id))
    conn.commit()
    conn.close()

def get_last_fetched(channel):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT last_message_id FROM last_fetched WHERE channel = ?", (channel,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def search_messages_by_keywords(keywords, limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pattern = "%" + "%".join(keywords) + "%"
    c.execute("""
        SELECT date, text FROM messages
        WHERE text LIKE ?
        ORDER BY date DESC
        LIMIT ?
    """, (pattern, limit))
    results = c.fetchall()
    conn.close()
    return [{'date': r[0], 'text': r[1]} for r in results]

def get_all_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM channels")
    results = c.fetchall()
    conn.close()
    return [r[0] for r in results]

def add_channel(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO channels (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def remove_channel(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def get_stats_per_channel():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel, COUNT(*) FROM messages GROUP BY channel")
    rows = c.fetchall()
    conn.close()
    return rows

def get_recent_messages(limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT date, text FROM messages
        ORDER BY date DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"date": row[0], "text": row[1]} for row in rows]

def get_unsummarized_messages(user_id, channel):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get the last summarized message ID for the user in the specified channel
    c.execute("""
        SELECT last_message_id FROM user_channel_updates
        WHERE user_id = ? AND channel = ?
    """, (user_id, channel))
    row = c.fetchone()
    last_id = row[0] if row else 0

    # get_last_fetched returns the last fetched message ID for the channel
    c.execute("""
        SELECT message_id, date, text FROM messages
        WHERE channel = ? AND message_id > ?
        ORDER BY message_id ASC
    """, (channel, last_id))
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "date": row[1], "text": row[2]} for row in rows]

def update_last_summarized(user_id, channel, message_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_channel_updates (user_id, channel, last_message_id)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, channel)
        DO UPDATE SET last_message_id = excluded.last_message_id
    """, (user_id, channel, message_id))
    conn.commit()
    conn.close()
