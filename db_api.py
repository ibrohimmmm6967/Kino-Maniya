import sqlite3

DB_NAME = "movies.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

# ================= MOVIES =================

def get_movie_by_code(code):
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT code, name, genre, file_id, views FROM movies WHERE code = ?",
        (code,)
    ).fetchone()
    conn.close()

    if row:
        return {
            "code": row[0],
            "name": row[1],
            "genre": row[2],
            "file_id": row[3],
            "views": row[4]
        }
    return None

def search_movies_by_name(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT code, name, genre, file_id, views FROM movies WHERE name LIKE ?",
        (f"%{keyword}%",)
    ).fetchall()
    conn.close()

    return [
        {
            "code": r[0],
            "name": r[1],
            "genre": r[2],
            "file_id": r[3],
            "views": r[4]
        } for r in rows
    ]

def get_movies_by_genre(genre):
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT code, name FROM movies WHERE lower(genre) = lower(?)",
        (genre,)
    ).fetchall()
    conn.close()
    return rows

def increment_views(code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE movies SET views = views + 1 WHERE code = ?",
        (code,)
    )
    conn.commit()
    conn.close()

def add_movie(code, name, genre, file_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO movies (code, name, genre, file_id, views)
        VALUES (?, ?, ?, ?, 0)
    """, (code, name, genre, file_id))
    conn.commit()
    conn.close()

def delete_movie(code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE code = ?", (code,))
    conn.commit()
    conn.close()

def get_top_movies(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT name, views FROM movies ORDER BY views DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows

def count_movies():
    conn = get_connection()
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    conn.close()
    return count

def sum_views():
    conn = get_connection()
    cursor = conn.cursor()
    total = cursor.execute("SELECT SUM(views) FROM movies").fetchone()[0]
    conn.close()
    return total or 0

# ================= EXTRA QUERIES =================

def get_all_movies():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT code, name, genre, file_id, views
        FROM movies
        ORDER BY name
    """)
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "code": r[0],
            "name": r[1],
            "genre": r[2],
            "file_id": r[3],
            "views": r[4],
        }
        for r in rows
    ]


def count_views():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT SUM(views) FROM movies")
    total = cur.fetchone()[0]
    conn.close()

    return total or 0
