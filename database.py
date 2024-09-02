import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

class Database:

    '''CREATE the Users TABLE'''
    def create_user_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        self.con.commit()

    '''Register a new user'''
    def register_user(self, username, password):
        hashed_password = generate_password_hash(password)
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            self.con.commit()
        except sqlite3.IntegrityError:
            return False  # Username already exists
        return True

    '''Authenticate the user'''
    def login_user(self, username, password):
        user = self.cursor.execute("SELECT password FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user[0], password):
            return True
        return False

    '''CREATE the Tasks TABLE'''
    def create_task_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task TEXT NOT NULL,
                due_date TEXT,
                completed BOOLEAN NOT NULL CHECK (completed IN (0,1)),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        self.con.commit()

    def add_user_id_column(self):
        try:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN user_id INTEGER")
            self.con.commit()
        except sqlite3.OperationalError:
            # Column already exists, so ignore this error
            pass

    def __init__(self):
        self.con = sqlite3.connect('todo.db')
        self.cursor = self.con.cursor()
        self.create_user_table()
        self.create_task_table()
        self.add_user_id_column()


    def create_user(self, username, password):
        self.cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, password))
        self.con.commit()

    def authenticate_user(self, username, password):
        user = self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                                   (username, password)).fetchone()
        return user


    '''CREATE A Task'''
    def create_task(self, user_id, task, due_date=None):
        self.cursor.execute("INSERT INTO tasks(user_id, task, due_date, completed) VALUES(?, ?, ?, ?)", (user_id, task, due_date, 0))
        self.con.commit()
        created_task = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE task = ? and completed = 0 AND user_id = ?", (task, user_id)).fetchall()
        return created_task[-1]

    '''READ / GET the tasks'''
    def get_tasks(self, user_id):
        complete_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 1 AND user_id = ?", (user_id,)).fetchall()
        incomplete_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 0 AND user_id = ?", (user_id,)).fetchall()
        return incomplete_tasks, complete_tasks

    '''UPDATING the tasks status'''

    def mark_task_as_complete(self, user_id, taskid):
        self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit()

    def mark_task_as_incomplete(self, user_id, taskid):
        self.cursor.execute("UPDATE tasks SET completed=0 WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit()

        # returning the task text
        task_text = self.cursor.execute("SELECT task FROM tasks WHERE id=? AND user_id=?", (taskid, user_id)).fetchall()
        return task_text[0][0] if task_text else None


    '''Deleting the task'''

    def delete_task(self, user_id, taskid):
        self.cursor.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit()

    '''Closing the connection '''

    def close_db_connection(self):
        self.con.close()