import sqlite3

def init_db():
    with sqlite3.connect("dados.db") as conn:
        cur = conn.cursor()
        cur.execute('''
            DROP TABLE sensores;
        ''')
        cur.execute('''
            DROP TABLE atuadores;
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sensores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                tipo TEXT,
                valor TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS atuadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                dispositivo TEXT,
                comando TEXT
            )
        ''')
        conn.commit()

init_db()