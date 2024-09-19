# Packages and dependencies
from kivymd.app import MDApp # Base class for Kivy MD app
from kivymd.uix.dialog import MDDialog # Class for creating dialogs
from kivymd.uix.boxlayout import MDBoxLayout # Layout to organise widgets in a box
from kivymd.uix.pickers import MDDatePicker # Date picker widget

from kivymd.uix.list import TwoLineAvatarIconListItem, ILeftBodyTouch # List item with two lines and an avatar/icon
from kivymd.uix.selectioncontrol import MDCheckbox # Checkbox widget

from datetime import datetime # For working with date and time for task creation

from kivy.uix.screenmanager import ScreenManager, Screen # Manages and switches between different screens
from kivy.uix.boxlayout import BoxLayout # Box layout for organizing widgets
from kivy.properties import ObjectProperty # Property that is referenced in KV file
from kivymd.uix.button import MDRaisedButton, MDFlatButton # Raised and flat button widgets
from kivymd.uix.textfield import MDTextField # Text input widget

from database import Database # Custom database class for app data

db = Database() # Initialises the database

# Creates the login screen
class LoginScreen(Screen): # Screen for user login
    def attempt_login(self, username, password): # Function to handle login attempts
        user = db.authenticate_user(username, password) # Check if the user exists in the database
        if user: # If user exists
            app = MDApp.get_running_app() # Get current app instance
            app.user_id = user[0]  # Store the logged-in user's ID
            app.root.current = 'main' # Switch to the main screen
        else: # If login failed
            self.ids.login_message.text = "Login failed. Please check your username and password." # Show error message

    def open_register_dialog(self): # Function to open the registration dialog
        if not hasattr(self, 'register_dialog'): # Check if the dialog already exists
            self.register_dialog = MDDialog( # Create a registration dialog if not already open
                title="Register",
                type="custom",
                content_cls=RegisterContent(), # Content of the registration form
                buttons=[ # Buttons in the dialog

                    MDRaisedButton( # Register user button
                        text="REGISTER",
                        on_release=self.register_user
                    ),
                    MDFlatButton( # Cancel button
                        text="CANCEL",
                        on_release=self.close_register_dialog
                    ),
                ],
            )
        self.register_dialog.open() # Open the dialog

    def register_user(self, *args): # Function to register a new user
        register_content = self.register_dialog.content_cls # Get the content of the dialog
        username = register_content.ids.username.text # Get username input
        password = register_content.ids.password.text # Get password input

        if username and password: # If username and password are provided
            try:
                db.create_user(username, password) # Try to create a new user in the database
                self.ids.login_message.text = "Registration successful! You can now log in." # Show success message
                self.close_register_dialog() # Close the dialog
            except Exception as e: # If registration fails
                self.ids.login_message.text = f"Registration failed: {str(e)}" # Show error message
        else: # If either field is empty
            self.ids.login_message.text = "Please enter both a username and password." # Show validation message

    def close_register_dialog(self, *args): # Close the registration dialog
        self.register_dialog.dismiss() # Close/dismiss the dialog

class RegisterContent(MDBoxLayout): # Custom layout for registration dialog content
    pass

    def validate_user(self): # Validate user login attempt
        if db.login_user(self.username.text, self.password.text): # Check credentials
            self.manager.current = "main"  # Switch to the main screen if valid
        else:
            print("Invalid credentials")  # Print error message

# Create the registration screen
class RegisterScreen(Screen): # Screen for user registration
    username = ObjectProperty(None) # Reference to username input from KV file
    password = ObjectProperty(None) # Reference to password input from KV file

    def register(self): # Function to register the user
        if db.register_user(self.username.text, self.password.text): # Register user in the database
            print("User registered successfully") # Print success message
            self.manager.current = "login"  # Switch back to the login screen
        else:
            print("Username already exists") # Print error if username exists

# Main task screen
class MainScreen(Screen): # Screen to display tasks
    pass

class ProfileScreen(Screen): # Screen to display user profile
    username = "Admin" # Default username
    password = "********" # Default password
    total_tasks_created = 52 # Example total tasks created
    total_tasks_completed = 46 # Example total tasks completed


class DialogContent(MDBoxLayout): # Custom layout for dialog content
    """Opens a Dialog Box That Gets The Task From The User"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.date_text.text = str(datetime.now().strftime('%A %d %B %Y')) # Set the date in the dialog

    #This function will show the date picker
    def show_date_picker(self): # Open a date picker to select a due date
        """Opens the date picker"""
        date_dialog = MDDatePicker() # Create the date picker
        date_dialog.bind(on_save=self.on_save) # Bind save function to save the selected date
        date_dialog.open() # Open the date picker

    #This function will get the date and save it in a good form
    def on_save(self, instance, value, date_range): # Callback function after picking a date
        date = value.strftime('%A %d %B %Y') # Format the date
        self.ids.date_text.text = str(date) # Set the selected date in the UI

# Class for marking and deleting the list item
class ListItemWithCheckbox(TwoLineAvatarIconListItem): # List item class with checkbox functionality
    def __init__(self, pk=None, **kwargs):
        super().__init__(**kwargs)
        self.pk = pk # Store the primary key (task ID)

    # Marking the item as complete or incomplete
    def mark(self, check, the_list_item): # Function to mark task as complete or incomplete
        '''Mark the task as complete or incomplete'''
        app = MDApp.get_running_app()  # Get the running app instance
        if check.active: # If checkbox is checked
            the_list_item.text = '[s]' + the_list_item.text + '[/s]' # Strike-through the text to indicate completion
            db.mark_task_as_complete(app.user_id, self.pk)  # Mark the task as complete in the database
        else: # If checkbox is unchecked
            the_list_item.text = str(db.mark_task_as_incomplete(app.user_id, self.pk))  # Mark as incomplete in the database

    # Deleting the list item
    def delete_item(self, the_list_item): # Function to delete the task
        '''Delete the task'''
        app = MDApp.get_running_app()  # Get the running app instance
        self.parent.remove_widget(the_list_item) # Remove the item from the UI
        db.delete_task(app.user_id, self.pk)  # Delete the task from the database

class LeftCheckbox(ILeftBodyTouch, MDCheckbox): # Custom checkbox widget for the task item
    '''Custom left container'''


#This is the main App class
class MainApp(MDApp): # Main app class inheriting from MDApp
    task_list_dialog = None # Dialog instance for creating tasks
    user_id = None # Variable to store the logged-in user's ID

    def login_user(self, username, password): # Function to log in a user
        user = db.authenticate_user(username, password) # Authenticate the user
        if user:
            self.user_id = user[0]  # Store user ID after login
            self.load_tasks()  # Load the user's tasks
        else:
            print("Login failed") # Print failure message if login fails

    def load_tasks(self): # Load all tasks (incomplete and complete) from the database
        incompleted_tasks, completed_tasks = db.get_tasks(self.user_id) # Get tasks from the database
        self.root.ids.container.clear_widgets() # Clear the current task list in the UI

        for task in incompleted_tasks: # Add incomplete tasks to the list
            add_task = ListItemWithCheckbox(pk=task[0], text=str(task[1]), secondary_text=task[2])
            self.root.ids.container.add_widget(add_task)

        for task in completed_tasks: # Add completed tasks to the list
            add_task = ListItemWithCheckbox(pk=task[0], text='[s]' + str(task[1]) + "[/s]", secondary_text=task[2])
            add_task.ids.check.active = True
            self.root.ids.container.add_widget(add_task)


    #This is the build function for setting the theme
    def build(self):
        self.task_list_dialog = None
        self.theme_cls.primary_palette = "Amber"

        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(ProfileScreen(name="profile"))
        return sm

        # This is the show task function

    def show_task_dialog(self):
        if not self.task_list_dialog:
            self.task_list_dialog = MDDialog(
                title="Create Task",
                type="custom",
                content_cls=DialogContent(),
            )
        self.task_list_dialog.open()
    def on_start(self):
        # Load tasks if user_id is set
        if self.user_id is not None:
            incompleted_tasks, completed_tasks = db.get_tasks(self.user_id) # Get incomplete and completed tasks for the current user from the database
            self.root.ids.container.clear_widgets()  # Clear the current task container (UI element) so it can be replaced with fresh data
            for task in incompleted_tasks: # Loop through each incomplete task and add it to the UI with a checkbox
                add_task = ListItemWithCheckbox(pk=task[0], text=str(task[1]), secondary_text=task[2])
                self.root.ids.container.add_widget(add_task) # Add the incomplete task widget to the container
            for task in completed_tasks: # Loop through each completed task, add it to the UI with a strikethrough on the task text
                add_task = ListItemWithCheckbox(pk=task[0], text='[s]' + str(task[1]) + "[/s]", secondary_text=task[2])
                add_task.ids.check.active = True # Mark the checkbox as active (completed)
                self.root.ids.container.add_widget(add_task) # Add the completed task widget to the container

    # This is a dialog closing function
    def close_dialog(self, *args): # Close the task creation dialog
        if self.task_list_dialog: # If the task dialog exists (is open), dismiss it
            self.task_list_dialog.dismiss() # Close the dialog window
            self.task_list_dialog = None # Reset the dialog to None (indicating it’s closed)

    # Add a new task and save it in the database
    def add_task(self, task, task_date):
        if task.text: # Ensure that the task text field is not empty
            created_task = db.create_task(self.user_id, task.text, task_date) # Save the new task into the database for the current user, returning the created task

            # Add the newly created task to the UI (task list in the 'main' screen)
            self.root.get_screen('main').ids['container'].add_widget(
                ListItemWithCheckbox(
                    pk=created_task[0], # Primary key (ID) of the task
                    text=str(created_task[1]), # Task text
                    secondary_text=created_task[2] # Task date or any other detail
                )
            )
            # Clear the task text input field after adding the task
            task.text = ''
            self.close_dialog()  # Close the task creation dialog after adding the task

    def mark_task_as_complete(self, user_id, taskid): # Mark a task as completed in the database
        self.cursor.execute("UPDATE tasks SET completed=1 WHERE id=? AND user_id=?", (taskid, user_id)) # Update the task in the database, setting its status to 'completed' (completed=1)
        self.con.commit() # Commit the transaction to save the changes in the database

    def mark_task_as_incomplete(self, taskid): # Mark a task as incomplete in the database
        db.mark_task_as_incomplete(self.user_id, taskid)  # Use the database method to mark the task as incomplete for the current user

    def delete_task(self, user_id, taskid): # Delete a task from the database
        self.cursor.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (taskid, user_id))  # Delete the task from the database for the current user and task ID
        self.con.commit() # Commit the transaction to confirm the deletion

    def open_profile_screen(self): # Open the profile screen of the application
        # Logic to open the profile screen
        self.root.current = 'profile_screen' # Switch to the 'profile_screen' screen in the application

if __name__ == '__main__': # If the script is being run directly (not imported as a module)
    app = MainApp() # Create an instance of the MainApp class
    app.run() # Run the application