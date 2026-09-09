import sqlite3
import os
from flask import g, current_app

DATABASE_NAME = 'tasks.db'

def get_db_path():
    """Returns the absolute path to the SQLite database file."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_dir, DATABASE_NAME)

def get_db():
    """
    Connect to the SQLite database.
    Stores the active connection in Flask's application context `g`.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        # Allows accessing columns by name like dict: row['title']
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    """Closes database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database using schema.sql."""
    db_path = get_db_path()
    schema_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'schema.sql')

    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def migrate_db_if_needed():
    """Checks for existing database schema and performs non-destructive migrations."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]

    if columns and 'category' not in columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN category TEXT NOT NULL DEFAULT 'General'")
        conn.commit()

    conn.close()

def seed_sample_data_if_empty():
    """Seeds initial starter tasks so the user sees a rich UI on first launch."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    if not cursor.fetchone():
        conn.close()
        init_db()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

    # Apply migration in case table was created with an earlier schema
    cursor.execute("PRAGMA table_info(tasks)")
    cols = [col[1] for col in cursor.fetchall()]
    if 'category' not in cols:
        cursor.execute("ALTER TABLE tasks ADD COLUMN category TEXT NOT NULL DEFAULT 'General'")
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    
    if count == 0:
        sample_tasks = [
            (
                'Welcome to TaskFlow! 👋',
                'Explore the dashboard, try dark mode, and mark this task as completed.',
                'Personal',
                '2026-09-15',
                'Low',
                'Completed'
            ),
            (
                'Complete Python Flask Tutorial',
                'Review routes, Jinja2 templates, and SQLite integration for beginner mastery.',
                'Study',
                '2026-09-12',
                'High',
                'Pending'
            ),
            (
                'Design Portfolio Project Section',
                'Document the architecture, features, and screenshots of this Personal Task Manager.',
                'Work',
                '2026-09-20',
                'Medium',
                'Pending'
            ),
            (
                'Weekly Grocery Shopping',
                'Pick up fresh vegetables, fruits, almond milk, and coffee beans.',
                'Personal',
                '2026-09-10',
                'Low',
                'Pending'
            )
        ]
        cursor.executemany(
            """
            INSERT INTO tasks (title, description, category, due_date, priority, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_tasks
        )
        conn.commit()

    conn.close()

def init_app(app):
    """Registers database teardown, migration, and initialization with Flask application."""
    app.teardown_appcontext(close_db)
    migrate_db_if_needed()
    seed_sample_data_if_empty()
