import sqlite3 # Import the sqlite3 library for database operations
from werkzeug.security import generate_password_hash, check_password_hash # Import password hashing utilities from werkzeug

# Class for managing the database operations
class Database:

    '''CREATE the Users TABLE'''
    def create_user_table(self): # Create a 'users' table if it doesn't exist, with columns for id, username, and password
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        self.con.commit() # Commit the changes to the database

    '''Register a new user'''
    def register_user(self, username, password):
        hashed_password = generate_password_hash(password)  # Hash the user's password before storing it
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password)) # Insert the new user into the 'users' table
            self.con.commit() # Commit the changes
        except sqlite3.IntegrityError:
            return False  # Return False if username already exists (violates the unique constraint)
        return True # Return True if registration was successful

    '''Authenticate the user'''
    def login_user(self, username, password):
        user = self.cursor.execute("SELECT password FROM users WHERE username=?", (username,)).fetchone() # Query the 'users' table for the password corresponding to the provided username
        if user and check_password_hash(user[0], password):
            return True # Return True if login is successful
        return False # Return False if login fails

    '''CREATE the Tasks TABLE'''
    def create_task_table(self):
        # Create a 'tasks' table if it doesn't exist, with columns for task details and user association
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
        self.con.commit() # Commit the changes

    # Adds a 'user_id' column to the 'tasks' table if it doesn't exist
    def add_user_id_column(self):
        try:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN user_id INTEGER")
            self.con.commit() # Commit the change if the column is added
        except sqlite3.OperationalError: # Ignore the error if the column already exists
            pass

    # Initialisation method to set up the database connection and create tables
    def __init__(self):
        self.con = sqlite3.connect('todo.db') # Connect to the 'todo.db' SQLite database
        self.cursor = self.con.cursor() # Create a cursor object to execute SQL commands
        self.create_user_table() # Create the 'users' table
        self.create_task_table() # Create the 'tasks' table
        self.add_user_id_column() # Ensure the 'user_id' column is present in the 'tasks' table

    # Manually create a user
    def create_user(self, username, password):
        self.cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, password))
        self.con.commit() # Commit the changes

    # Authenticate the user by checking both the username and password
    def authenticate_user(self, username, password):
        user = self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                                   (username, password)).fetchone()
        return user # Return the user if found, or None if authentication fails


    '''CREATE A Task'''
    def create_task(self, user_id, task, due_date=None):
        self.cursor.execute("INSERT INTO tasks(user_id, task, due_date, completed) VALUES(?, ?, ?, ?)", (user_id, task, due_date, 0)) # Insert a new task into the 'tasks' table with the provided user_id, task description, due date, and default completion status (0 = incomplete)
        self.con.commit() # Commit the changes
        created_task = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE task = ? and completed = 0 AND user_id = ?", (task, user_id)).fetchall() # Retrieve the task just created, filtering by the task description, user, and completion status
        return created_task[-1] # Return the last task created (in case of multiple matches)

    '''READ / GET the tasks'''
    def get_tasks(self, user_id):
        complete_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 1 AND user_id = ?", (user_id,)).fetchall() # Retrieve all completed tasks for the given user
        incomplete_tasks = self.cursor.execute("SELECT id, task, due_date FROM tasks WHERE completed = 0 AND user_id = ?", (user_id,)).fetchall()  # Retrieve all incomplete tasks for the given user
        return incomplete_tasks, complete_tasks # Return both incomplete and complete tasks

    '''UPDATING the tasks status'''
    # Mark a task as completed by setting the 'completed' field to 1 for the given user and task ID
    def mark_task_as_complete(self, user_id, taskid):
        self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit() # Commit the changes

    # Mark a task as incomplete by setting the 'completed' field to 0 for the given user and task ID
    def mark_task_as_incomplete(self, user_id, taskid):
        self.cursor.execute("UPDATE tasks SET completed=0 WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit() # Commit the changes
        # Retrieve and return the task description (text) after marking it as incomplete
        task_text = self.cursor.execute("SELECT task FROM tasks WHERE id=? AND user_id=?", (taskid, user_id)).fetchall()
        return task_text[0][0] if task_text else None # Return task text if it exists, else return None


    '''Deleting the task'''
    # Delete a task from the 'tasks' table for the given user and task ID
    def delete_task(self, user_id, taskid):
        self.cursor.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (taskid, user_id))
        self.con.commit() # Commit the changes

    '''Closing the connection '''
    # Close the database connection
    def close_db_connection(self):
        self.con.close()