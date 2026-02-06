import sqlite3

DB_NAME = "recommendation.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
    """)

    # USER INTERACTIONS (LIKE / DISLIKE)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # USER PREFERENCES (Q-VALUES + INTERACTION COUNT)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS preferences (
        user_id INTEGER,
        category TEXT,
        score REAL DEFAULT 0,
        interactions INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, category)
    )
""")

    # SAVED ARTICLES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS saved_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            url TEXT,
            category TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # REWARD LOG TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reward_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reward INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_user(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    user = cur.fetchone()

    if user:
        user_id = user[0]
    else:
        cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user_id = cur.lastrowid
        conn.commit()

    conn.close()
    return user_id


def save_interaction(user_id, category, action):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO interactions (user_id, category, action)
        VALUES (?, ?, ?)
    """, (user_id, category, action))

    conn.commit()
    conn.close()


def get_preferences(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT category, score FROM preferences WHERE user_id=?",
        (user_id,)
    )

    data = cur.fetchall()
    conn.close()

    return {cat: score for cat, score in data}


def update_preference(user_id, category, reward, alpha=0.1):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT score FROM preferences WHERE user_id=? AND category=?",
        (user_id, category)
    )

    row = cur.fetchone()
    old_q = row[0] if row else 0

    # 🔹 True Q-learning update
    new_q = old_q + alpha * (reward - old_q)

    cur.execute("""
        INSERT INTO preferences (user_id, category, score)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, category)
        DO UPDATE SET score=?
    """, (user_id, category, new_q, new_q))

    conn.commit()
    conn.close()


def save_article(user_id, title, url, category):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO saved_articles (user_id, title, url, category)
        VALUES (?, ?, ?, ?)
    """, (user_id, title, url, category))

    conn.commit()
    conn.close()


def get_saved_articles(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, url, category, timestamp
        FROM saved_articles
        WHERE user_id=?
        ORDER BY timestamp DESC
    """, (user_id,))

    articles = cur.fetchall()
    conn.close()

    return articles


def get_global_category_scores():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT category, COUNT(*) as count
        FROM interactions
        WHERE action = 'like'
        GROUP BY category
    """)

    data = cur.fetchall()
    conn.close()

    return {category: count * 0.2 for category, count in data}


def log_reward(user_id, reward):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO reward_log (user_id, reward) VALUES (?, ?)",
        (user_id, reward)
    )

    conn.commit()
    conn.close()


def get_reward_history(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT reward FROM reward_log WHERE user_id=?",
        (user_id,)
    )

    rewards = [r[0] for r in cur.fetchall()]
    conn.close()

    return rewards

