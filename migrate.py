import json
import sqlite3

DB_NAME = "movies.db"

with open("movies_db.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

for code, movie in movies.items():
    cursor.execute("""
        INSERT OR IGNORE INTO movies (code, name, genre, file_id, views)
        VALUES (?, ?, ?, ?, ?)
    """, (
        code,
        movie.get("name"),
        movie.get("genre", "Noma"),
        movie.get("file_id"),
        movie.get("views", 0)
    ))

conn.commit()
conn.close()

print("✅ JSON → SQLite o‘tkazildi!")
