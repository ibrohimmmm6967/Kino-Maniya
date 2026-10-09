import sqlite3

conn = sqlite3.connect("movies.db")
cursor = conn.cursor()

rows = cursor.execute("SELECT code, name, genre, views FROM movies").fetchall()

for row in rows:
    print(row)

conn.close()
