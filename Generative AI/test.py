import sqlite3

# Connect to SQLite
conn = sqlite3.connect("chat.db")
cursor = conn.cursor()

# Create table with unique (sessionid, route)
cursor.execute("""
CREATE TABLE IF NOT EXISTS session_thread (
    sessionid TEXT NOT NULL,
    route TEXT NOT NULL,
    threadid INTEGER NOT NULL,
    PRIMARY KEY (sessionid, route)
)
""")
conn.commit()

def insert_session_thread(sessionid: str, route: str) -> int:
    """
    Inserts a new (sessionid, route) with a unique threadid.
    If it already exists, returns the existing threadid.
    Threadid increments globally.
    """
    # Check if the pair already exists
    cursor.execute("""
        SELECT threadid
        FROM session_thread
        WHERE sessionid = ? AND route = ?
    """, (sessionid, route))
    row = cursor.fetchone()
    
    if row:
        return row[0]  # Return existing threadid

    # Get the current max threadid globally
    cursor.execute("SELECT COALESCE(MAX(threadid), 0) FROM session_thread")
    max_threadid = cursor.fetchone()[0]
    new_threadid = max_threadid + 1

    # Insert new row
    cursor.execute("""
        INSERT INTO session_thread (sessionid, route, threadid)
        VALUES (?, ?, ?)
    """, (sessionid, route, new_threadid))
    conn.commit()

    return new_threadid

# Example usage
print(insert_session_thread("sess1", "payment"))  # → 1
print(insert_session_thread("sess1", "payment"))  # → 1 (same as before)
print(insert_session_thread("sess1", "order"))    # → 2
print(insert_session_thread("sess2", "payment"))  # → 3
print(insert_session_thread("sess1", "order"))    # → 2 (same as before)

# Check table contents
cursor.execute("SELECT * FROM session_thread ORDER BY threadid")
for row in cursor.fetchall():
    print(row)

conn.close()
